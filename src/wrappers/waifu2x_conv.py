#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name: Dandere2X waifu2x-conv
Author: CardinalPanda
Date Created: March 22, 2019
Last Modified: April 2, 2019

Description: # A pretty hacky wrapper for Waifu2x-Conveter-Cpp.
Behaves pretty similair to waifu2x-caffe, except directory must be
set  (for subprocess call) and arguments are slightly different.
Furthermore, waifu2x-conv-caffe saves files in an annoying way,
so we need to correct those odd namings.
"""
from dandere2x_core.dandere2x_utils import get_lexicon_value
from dandere2x_core.dandere2x_utils import rename_file
import logging
import os
import subprocess
import threading


class Waifu2xConv(threading.Thread):

    def __init__(self, workspace, frame_count, waifu2x_conv_dir, waifu2x_conv_dir_dir, output_dir, upscaled_dir,
                 noise_level, scale_factor):

        self.frame_count = frame_count
        self.waifu2x_conv_dir = waifu2x_conv_dir
        self.waifu2x_conv_dir_dir = waifu2x_conv_dir_dir
        self.output_dir = output_dir
        self.upscaled_dir = upscaled_dir
        self.noise_level = noise_level
        self.scale_factor = scale_factor
        self.workspace = workspace
        threading.Thread.__init__(self)
        logging.basicConfig(filename=self.workspace + 'waifu2x.log', level=logging.INFO)

    # manually upscale a single file
    @staticmethod
    def upscale_file(workspace, waifu2x_conv_dir, waifu2x_conv_dir_dir, input_file, output, noise_level, scale_factor):
        logger = logging.getLogger(__name__)

        exec = [waifu2x_conv_dir,
                "-i", input_file,
                "-o", output,
                "--model-dir", waifu2x_conv_dir_dir + "models_rgb",
                "--force-OpenCL",
                "-s",
                "--noise-level", noise_level,
                "--scale-ratio", scale_factor]

        os.chdir(waifu2x_conv_dir_dir)

        logger.info("manually upscaling file")
        logger.info(exec)
        subprocess.run(exec)

    # Waifu2x-Converter-Cpp adds this ugly '[NS-L3][x2.000000]' to files, so
    # this function just renames the files so Dandere2x can interpret them correctly.
    def fix_names(self):
        list = os.listdir(self.upscaled_dir)
        for name in list:
            if '[NS-L3][x' + self.scale_factor + '.000000]' in name:
                rename_file(self.upscaled_dir + name, self.upscaled_dir + name.replace('_[NS-L3][x' + self.scale_factor + '.000000]', ''))

    def run(self):
        logger = logging.getLogger(__name__)

        # if there are pre-existing files, fix them (this occurs during a resume session)
        self.fix_names()

        # we need to os.chdir or else waifu2x-conveter won't work.
        os.chdir(self.waifu2x_conv_dir_dir)

        # calling waifu2x-conv command
        exec = [self.waifu2x_conv_dir,
                "-i", self.output_dir,
                "-o", self.upscaled_dir,
                "--model-dir", self.waifu2x_conv_dir_dir + "models_rgb",
                "--force-OpenCL",
                "-s",
                "--noise-level", self.noise_level,
                "--scale-ratio", self.scale_factor]

        logger.info("waifu2xconv session")
        logger.info(exec)

        # make a list of names that will eventually (past or future) be upscaled
        names = []
        for x in range(1, self.frame_count):
            names.append("output_" + get_lexicon_value(6, x) + ".png")

        count_removed = 0

        # remove from the list images that have already been upscaled
        for item in names[::-1]:
            if os.path.isfile(self.upscaled_dir + item):
                names.remove(item)
                count_removed += 1

        if count_removed:
            logger.info("Already have " + str(count_removed) + " upscaled")

        # while there are pictures that have yet to be upscaled, keep calling the upscale command
        while names:
            logger.info("Frames remaining before batch: ")
            logger.info(len(names))
            subprocess.run(exec)
            self.fix_names()
            for item in names[::-1]:
                if os.path.isfile(self.upscaled_dir + item):
                    os.remove(self.output_dir + item)
                    names.remove(item)
