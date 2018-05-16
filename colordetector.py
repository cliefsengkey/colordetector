"""
    dependencies:
    pip install networkx==1.11
    pip install colormath==2.1.1
    pip install colors.py==0.2.2
    pip install webcolors==1.7
    pip install colorthief==0.2.1
    pip install opencv-python==3.3.0.10

    example of using:
    import color_similarity as c
    brand_color = '#D1D7AF'
    c.get_similar_color(brand_color,k=3) # value of k is the number of top-k
    color to be returned *optional
"""
from __future__ import unicode_literals
import os

from colors import rgb, hex
import webcolors as wc
from colorthief import ColorThief
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

import pandas as pd
import numpy as np
import cv2
import urllib.request
import os

df = pd.read_csv('color_lists.csv', sep=',')
# df.loc[df['level'] == 2]

class ColorDetector:
    # def __init__(self):

    def rgb_to_lab(self,rgb):
        """
            a method to conver tuple of RGB to LabColor
        """
        srgb = sRGBColor(float(
            float(rgb[0])/255.0), float(float(rgb[1])/255.0), float(float(rgb[2])/255.0))
        return convert_color(srgb, LabColor)

    def color_similarity(self,hex1, hex2):
        """
            a method to find similarity between 2 hex colors
        """
        if not hex1.startswith('#'):
            hex1 = '#'+hex1
        if not hex2.startswith('#'):
            hex2 = '#'+hex2
        rgb1 = wc.hex_to_rgb(hex1)
        rgb2 = wc.hex_to_rgb(hex1)
        return delta_e_cie2000(self.rgb_to_lab(rgb1), self.rgb_to_lab(rgb2))

    def get_similar_colors(self,brand_color, k=2, level=2):
        """
            this method is aim to find similar colors from YUNA color database to the given color -> 'brand_color'
            the input of brand_color can be tuple of rgb e.g. (0,5,0) or a Color Hex with/without '#' e.g. #FFF or FFFFFF
        """
        pair_list = []
        result_list = []
        for index,yuna_color in df.loc[df['level'] == level].iterrows():
            pair_dict = {}
            pair_dict['color'] = yuna_color['short_name']
            if isinstance(brand_color, tuple):
                y_c = (yuna_color['r_color'], yuna_color['g_color'], yuna_color['b_color'])
                cs = delta_e_cie2000(self.rgb_to_lab(brand_color), self.rgb_to_lab(y_c))
            else:
                if (not brand_color.startswith('#') and (len(brand_color) == 3 or len(brand_color) == 6)) or (brand_color.startswith('#') and (len(brand_color) == 4 or len(brand_color) == 7)):
                    cs = self.color_similarity(brand_color, yuna_color['hex_color'])
                else:
                    return None
            pair_dict['similarity'] = cs
            pair_list.append(pair_dict)

        result = sorted(pair_list, key=lambda k: k['similarity'], reverse=False)[:k]
        for i in result:
            result_list.append(i['color'])
        return result_list


    def remove_image_bg(self,img_name):
        """
            this method is aim to remove the backgroud of image to make it transparent.

        """
        img2_name = '%s_removed.png' % img_name
        # cv2.namedWindow('image', cv2.WINDOW_NORMAL)

        # Load the Image
        imgo = cv2.imread(img_name)
        height, width = imgo.shape[:2]

        # Create a mask holder
        mask = np.zeros(imgo.shape[:2], np.uint8)

        # Grab Cut the object
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)

        # Hard Coding the Rect
        rect = (10, 10, width-30, height-30)
        cv2.grabCut(imgo, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        mask = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        img1 = imgo*mask[:, :, np.newaxis]

        # Get the background
        background = imgo - img1

        # Change all pixels in the background that are not black to white
        background[np.where((background > [0, 0, 0]).all(axis=2))] = [
            255, 255, 255]

        # Add the background and the image
        final = background + img1
        cv2.imwrite(img2_name, final)
        return img2_name

    def get_image_color(self,img_name,additional_color=2,delete_temp=True):
        """
                Dependencies:
                pip install colorthief
                pip install opencv-python

                This method is aim to to find the main_color and additional color of an image
                The parameter of input is the URL of an image
                delete_temp default is False, if True then the temp image will be removed after get the colors
        """
        color_list = {}
        # img_name = "temp.jpg"
        # download image from url to local:
        # urllib.request.urlretrieve(img_url, img_name)

        img2_name = self.remove_image_bg(img_name)
        color_thief = ColorThief(img2_name)
        # dominant_color = color_thief.get_color(quality=1)
        palette_colors = color_thief.get_palette(color_count=additional_color,quality=10)
        # dominant_color = self.get_similar_colors(dominant_color, k=1)
        additional_colors = []

        for color in palette_colors:
            additional = self.get_similar_colors(color, k=1)
            additional_colors.append(additional)

        # color_list['main_color'] = dominant_color[0]
        # color_list['additional_colors'] = additional_colors
        if delete_temp:
        #     os.remove("temp.jpg")
            os.remove("%s_removed.png" % img_name)

        return sum(additional_colors,[])
