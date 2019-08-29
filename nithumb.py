#!/usr/bin/python3

# Authors: John Cupitt <jcupitt@imperial.ac.uk>
# 
# Ported to pyvips from nithumb by 
#   Ghislain Antony Vaillant <g.vaillant@imperial.ac.uk>
#   Jonathan Passerat-Palmbach <j.passerat-palmbach@imperial.ac.uk>

from __future__ import division

from argparse import ArgumentParser
import sys
import pyvips

def parse_args():
    DESCRIPTION = 'Generate a thumbnail from a NIfTI file'

    parser = ArgumentParser(prog='nithumb', description=DESCRIPTION)
    parser.add_argument('inputfile', help='input NIfTI file')
    parser.add_argument('snapshot', help='output snapshot')
    parser.add_argument('thumbnail', help='output thumbnail')
    parser.add_argument('--snapshot_size', '-ss', 
        type=int, nargs=2, default=(128, 128), help='size of the snapshot')
    parser.add_argument('--thumbnail_size', '-ts', 
        type=int, nargs=2, default=(64, 64), help='size of the thumbnail')
    parser.add_argument('--percentile', '-p', 
        type=int, default=0, help='percentile to exclude')

    return parser.parse_args()

parsed = parse_args()

image = pyvips.Image.new_from_file(parsed.inputfile)

# check that we have the metadata we expect for a nifti file
if image.get_typeof("nifti-nx") == 0:
    print("not a nifti file")
    sys.exit(1)

# Scale in two stages: first, rescale to 0 - 255, then find the cumulative 
# histogram, exclude the top and bottom 5%, and scale again. 
image = image.scaleimage()
hist = image.hist_find().hist_cum()
total = hist(255, 0)[0]
five_percent = total * parsed.percentile / 100
ninety_five_percent = total * (100 - parsed.percentile) / 100
low = 0
high = 255
for i in range(0, 255):
    value = hist(i, 0)[0]
    if value < five_percent:
        low = i
    if value < ninety_five_percent:
        high = i

# print(f"low = {low}, high = {high}")
if high - low > 0:
    image = ((image - low) * (255 / (high - low))).cast("uchar")

# Select the centre slice.
nx = int(image.get("nifti-nx"))
ny = int(image.get("nifti-ny"))
nz = int(image.get("nifti-nz"))
image = image.crop(0, ny * (nz // 2), nx, ny)

# Generate and save the snapshot and its thumbnail.
snapshot = image.thumbnail_image(parsed.snapshot_size[0],
                                 height=parsed.snapshot_size[1])
snapshot.write_to_file(parsed.snapshot)

thumbnail = image.thumbnail_image(parsed.thumbnail_size[0],
                                  height=parsed.thumbnail_size[1])
thumbnail.write_to_file(parsed.thumbnail)

