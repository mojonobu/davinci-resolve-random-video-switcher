#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RandomVideoSwitcher - Video clip splitting script for DaVinci Resolve

Usage:
1. From Resolve console: Run directly in Fusion page console
2. From command line:
   set PYTHONPATH=%PROGRAMDATA%\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\
   python RandomVideoSwitcher.py
"""

import random

# ============================================
# Settings (can be changed later)
# ============================================
SPLIT_INTERVAL_SECONDS = 10  # Split interval (seconds)

# ============================================
# Step 1: Get and display basic information
# ============================================

# Connect to Resolve (supports both console and command line)
try:
    resolve = app.GetResolve()  # Run from Resolve console
    print("Mode: Resolve Console")
except NameError:
    import python_get_resolve
    resolve = python_get_resolve.GetResolve()  # Run from command line
    print("Mode: Command Line")

print("=" * 50)
print("RandomVideoSwitcher - Step 1: Get Basic Info")
print("=" * 50)

# Get project manager and current project.
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()

if project is None:
    print("Error: No project is open")
else:
    print(f"Project: {project.GetName()}")

    # Get current timeline
    timeline = project.GetCurrentTimeline()

    if timeline is None:
        print("Error: No timeline is selected")
    else:
        print(f"Timeline: {timeline.GetName()}")

        # Get frame rate
        fps_str = project.GetSetting('timelineFrameRate')
        fps = float(fps_str)
        print(f"Frame Rate: {fps} fps")

        # Calculate frames per split interval
        interval_frames = int(fps * SPLIT_INTERVAL_SECONDS)
        print(f"Split Interval: {SPLIT_INTERVAL_SECONDS}s = {interval_frames} frames")

        print("=" * 50)
        print("Step 1 Complete")
        print("=" * 50)

        # ============================================
        # Step 2: Get video track and clip information
        # ============================================
        print("")
        print("=" * 50)
        print("RandomVideoSwitcher - Step 2: Get Clip Info")
        print("=" * 50)

        # Get video track count
        video_track_count = timeline.GetTrackCount('video')
        print(f"Video Track Count: {video_track_count}")

        # Display clip information for each video track
        for track_index in range(1, video_track_count + 1):
            print(f"\n--- Video Track {track_index} ---")

            # Get items in track
            items = timeline.GetItemListInTrack('video', track_index)

            if not items:
                print("  No clips")
                continue

            print(f"  Clip Count: {len(items)}")

            for i, item in enumerate(items):
                print(f"\n  [{i + 1}] {item.GetName()}")
                print(f"      Timeline: start={item.GetStart()}, end={item.GetEnd()}, duration={item.GetDuration()}")
                print(f"      Source: start={item.GetSourceStartFrame()}, end={item.GetSourceEndFrame()}")

        print("")
        print("=" * 50)
        print("Step 2 Complete")
        print("=" * 50)

        # ============================================
        # Step 3-4: Split all clips on track 1
        # ============================================
        print("")
        print("=" * 50)
        print("RandomVideoSwitcher - Step 3-4: Split Track 1")
        print("=" * 50)

        # Get media pool
        mediaPool = project.GetMediaPool()

        # Split points (used in Step 6, obtained from actual positions after AppendToTimeline)
        split_points = []

        # Target all clips on video track 1
        track_index = 1
        items = timeline.GetItemListInTrack('video', track_index)

        if not items:
            print("Error: No clips on video track 1")
        else:
            print(f"Track 1 Clip Count: {len(items)}")

            # Collect all clip data first (before deletion)
            all_clip_data = []
            for item in items:
                clip_data = {
                    "name": item.GetName(),
                    "timeline_start": item.GetStart(),
                    "timeline_end": item.GetEnd(),
                    "duration": item.GetDuration(),
                    "source_start": item.GetSourceStartFrame(),
                    "source_end": item.GetSourceEndFrame(),
                    "media_pool_item": item.GetMediaPoolItem(),
                    "original_item": item
                }
                all_clip_data.append(clip_data)

            # Delete all clips
            print("\nDeleting original clips...")
            all_original_items = [data["original_item"] for data in all_clip_data]
            result = timeline.DeleteClips(all_original_items, False)
            print(f"  Delete result: {result}")

            # Split and recreate each clip
            all_new_clip_infos = []

            for clip_data in all_clip_data:
                clip_name = clip_data["name"]
                timeline_start = clip_data["timeline_start"]
                timeline_end = clip_data["timeline_end"]
                source_start = clip_data["source_start"]
                source_end = clip_data["source_end"]
                media_pool_item = clip_data["media_pool_item"]

                print(f"\nTarget clip: {clip_name}")
                print(f"  Timeline: start={timeline_start}, end={timeline_end}")
                print(f"  Source: {source_start} - {source_end}")

                if media_pool_item is None:
                    print("  Warning: Could not get MediaPoolItem. Skipping.")
                    continue

                # Calculate split clip info
                current_pos = source_start
                current_timeline_pos = timeline_start
                segment_index = 0

                while current_pos < source_end:
                    segment_index += 1
                    # Calculate end frame for this segment
                    segment_end = min(current_pos + interval_frames, source_end)
                    segment_duration = segment_end - current_pos

                    clip_info = {
                        "mediaPoolItem": media_pool_item,
                        "startFrame": current_pos,
                        "endFrame": segment_end,
                        "trackIndex": track_index,
                        "recordFrame": current_timeline_pos,
                        "mediaType": 1  # 1 = Video only
                    }
                    all_new_clip_infos.append(clip_info)

                    print(f"  Segment {segment_index}: timeline={current_timeline_pos}, duration={segment_duration}")

                    # Move to next segment
                    current_pos = segment_end
                    current_timeline_pos += segment_duration

            # Create split clips
            print(f"\nCreating split clips... (total {len(all_new_clip_infos)} segments)")
            new_items = mediaPool.AppendToTimeline(all_new_clip_infos)

            if new_items:
                print(f"  Created: {len(new_items)} clips")
                # Get split points from actual positions
                split_points = sorted(set(item.GetStart() for item in new_items))
                print(f"\nRecorded split points (actual positions): {len(split_points)}")
            else:
                print("  Error: Failed to create clips")
                split_points = []

        print("")
        print("=" * 50)
        print("Step 3-4 Complete")
        print("=" * 50)

        # ============================================
        # Step 6: Split other tracks at same timing
        # ============================================
        print("")
        print("=" * 50)
        print("RandomVideoSwitcher - Step 6: Split Other Tracks")
        print("=" * 50)

        if video_track_count < 2:
            print("No other video tracks. Skipping.")
        elif not split_points:
            print("No split points. Skipping.")
        else:
            print(f"Split points: {split_points}")

            for track_index in range(2, video_track_count + 1):
                print(f"\n--- Processing Track {track_index} ---")

                items = timeline.GetItemListInTrack('video', track_index)

                if not items:
                    print("  No clips. Skipping.")
                    continue

                print(f"  Clip Count: {len(items)}")

                # Collect all clip data
                all_clip_data = []
                for item in items:
                    clip_data = {
                        "name": item.GetName(),
                        "timeline_start": item.GetStart(),
                        "timeline_end": item.GetEnd(),
                        "source_start": item.GetSourceStartFrame(),
                        "source_end": item.GetSourceEndFrame(),
                        "media_pool_item": item.GetMediaPoolItem(),
                        "original_item": item
                    }
                    all_clip_data.append(clip_data)

                # Delete all clips
                all_original_items = [data["original_item"] for data in all_clip_data]
                result = timeline.DeleteClips(all_original_items, False)
                print(f"  Delete result: {result}")

                # Split each clip at split points
                all_new_clip_infos = []

                for clip_data in all_clip_data:
                    clip_name = clip_data["name"]
                    timeline_start = clip_data["timeline_start"]
                    timeline_end = clip_data["timeline_end"]
                    source_start = clip_data["source_start"]
                    source_end = clip_data["source_end"]
                    media_pool_item = clip_data["media_pool_item"]

                    if media_pool_item is None:
                        print(f"  Warning: Could not get MediaPoolItem for {clip_name}. Skipping.")
                        continue

                    # Extract split points within this clip
                    clip_split_points = [p for p in split_points if timeline_start < p < timeline_end]

                    # Split clip at boundaries
                    # Segment boundaries: [timeline_start, split1, split2, ..., timeline_end]
                    boundaries = [timeline_start] + clip_split_points + [timeline_end]

                    print(f"  {clip_name}: splitting into {len(boundaries) - 1} segments")

                    for i in range(len(boundaries) - 1):
                        seg_timeline_start = boundaries[i]
                        seg_timeline_end = boundaries[i + 1]
                        seg_duration = seg_timeline_end - seg_timeline_start

                        # Calculate source position
                        offset_from_clip_start = seg_timeline_start - timeline_start
                        seg_source_start = source_start + offset_from_clip_start
                        seg_source_end = seg_source_start + seg_duration

                        clip_info = {
                            "mediaPoolItem": media_pool_item,
                            "startFrame": seg_source_start,
                            "endFrame": seg_source_end,
                            "trackIndex": track_index,
                            "recordFrame": seg_timeline_start,
                            "mediaType": 1
                        }
                        print(f"    seg[{i}]: start={seg_source_start}, end={seg_source_end}, duration={seg_duration}")
                        all_new_clip_infos.append(clip_info)

                # Create split clips
                if all_new_clip_infos:
                    new_items = mediaPool.AppendToTimeline(all_new_clip_infos)
                    if new_items:
                        print(f"  Created: {len(new_items)} clips")
                    else:
                        print("  Error: Failed to create clips")

        print("")
        print("=" * 50)
        print("Step 6 Complete")
        print("=" * 50)

        # ============================================
        # Step 7: Random selection and clip disable
        # ============================================
        print("")
        print("=" * 50)
        print("RandomVideoSwitcher - Step 7: Random Selection")
        print("=" * 50)

        # Collect clips from all video tracks and group by start position
        clips_by_start = {}  # {start_frame: [(track_index, clip), ...]}

        for track_index in range(1, video_track_count + 1):
            items = timeline.GetItemListInTrack('video', track_index)
            if not items:
                continue
            for item in items:
                start_frame = item.GetStart()
                if start_frame not in clips_by_start:
                    clips_by_start[start_frame] = []
                clips_by_start[start_frame].append((track_index, item))

        print(f"Group count (timeline positions): {len(clips_by_start)}")

        # Randomly select one from each group, disable others
        enabled_count = 0
        disabled_count = 0

        for start_frame in sorted(clips_by_start.keys()):
            clips = clips_by_start[start_frame]

            if len(clips) == 1:
                # Only one clip, keep enabled
                track_idx, clip = clips[0]
                clip.SetClipEnabled(True)
                enabled_count += 1
                print(f"  frame {start_frame}: track {track_idx} (single)")
            else:
                # Multiple clips, randomly select one
                selected_idx = random.randint(0, len(clips) - 1)

                for i, (track_idx, clip) in enumerate(clips):
                    if i == selected_idx:
                        clip.SetClipEnabled(True)
                        enabled_count += 1
                        print(f"  frame {start_frame}: track {track_idx} selected (/{len(clips)})")
                    else:
                        clip.SetClipEnabled(False)
                        disabled_count += 1

        print(f"\nEnabled clips: {enabled_count}")
        print(f"Disabled clips: {disabled_count}")

        print("")
        print("=" * 50)
        print("Step 7 Complete")
        print("=" * 50)

        print("")
        print("=" * 50)
        print("RandomVideoSwitcher Complete")
        print("=" * 50)
