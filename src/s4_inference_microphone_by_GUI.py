# -*- coding: future_fstrings -*-
#!/usr/bin/env python2
from __future__ import division
from __future__ import print_function

'''
$ python src/s4_inference_microphone_by_GUI.py -h
$ python src/s4_inference_microphone_by_GUI.py --device 0
'''       

if 1: # Set path
    import sys, os
    ROOT = os.path.dirname(os.path.abspath(__file__))+"/../" # root of the project
    sys.path.append(ROOT)
    
import numpy as np 
import cv2
import librosa
import matplotlib.pyplot as plt 
from collections import namedtuple
import types
import time 
# import argparse # do not import argparse. It conflicts with the lib_record_audio
import torch 
import torch.nn as nn

if 1: # my lib
    import utils.lib_commons as lib_commons
    import utils.lib_rnn as lib_rnn
    import utils.lib_augment as lib_augment
    import utils.lib_datasets as lib_datasets
    import utils.lib_ml as lib_ml
    import utils.lib_io as lib_io
    from utils.lib_gui import GuiForAudioClassification
    from utils.lib_record_audio import * # argparse comes crom here

# -- Settings
SRC_WEIGHT_PATH = ROOT + "weights/my.ckpt"
SRC_CLASSES_PATH = ROOT + "config/classes.names"
DST_AUDIO_FOLDER = ROOT + "data/data_tmp/"

# -- Main class for reading audio from microphone, doing inference, and display result
class AudioClassifierWithGUI(object):
    
    def __init__(self, src_weight_path, src_classes_path, dst_audio_folder):

        # Init model
        model, classes = lib_rnn.setup_default_RNN_model(src_weight_path, src_classes_path)
        self._CLASSES = classes
        print("Number of classes = {}, classes: {}".format(len(classes), classes))
        model.set_classes(classes)
        self._model = model        

        # Set up GUI
        self._gui = GuiForAudioClassification(classes, hotkey="R")

        # Set up audio recorder
        self._DST_AUDIO_FOLDER = dst_audio_folder
        self._recorder = AudioRecorder()

    def record_audio_and_classifiy(self,
            is_shout_out_result=False):
        model, classes = self._model, self._CLASSES
        gui, recorder = self._gui, self._recorder 

        # -- Record audio
        gui.enable_img1_self_updating()
        recorder.start_record(folder=self._DST_AUDIO_FOLDER)  # Start record
        while not gui.is_key_released():  # Wait for key released
            time.sleep(0.001)
        recorder.stop_record()  # Stop record

        # -- Do inference
        audio = lib_datasets.AudioClass(filename=recorder.filename)
        probs = model.predict_audio_label_probabilities(audio)
        predicted_idx = np.argmax(probs)
        predicted_label = classes[predicted_idx]
        max_prob = probs[predicted_idx]
        print("\nAll word labels: {}".format(classes))
        print("\nPredicted label: {}, probability: {}\n".format(
            predicted_label, max_prob))
        PROB_THRESHOLD = 0.8
        final_label  = predicted_label if max_prob > PROB_THRESHOLD else "none"
        
        # -- Update the image

        # Update image1: first stop self updating, 
        # then set recording_length and voice_intensity to zero
        gui.reset_img1() 

        # Update image 2: the prediction results
        gui.set_img2(
            final_label=final_label,
            predicted_label=predicted_label, 
            probability=max_prob, 
            length=audio.get_len_s(),
            valid_length=audio.get_len_s(), # TODO: remove the silent voice,
        )
        
        # Update image 3: the probability of each class
        gui.set_img3(probabilities=probs)
        
        # -- Shout out the results. e.g.: two is one
        if is_shout_out_result:
            lib_datasets.shout_out_result(
                recorder.filename, # Raw audio to shout out
                final_label,
                middle_word="is",
                cache_folder="data/examples/")

        return predicted_label, max_prob

    def is_key_quit_pressed(self):
        return self._gui.is_key_quit_pressed()

    def is_key_pressed(self):
        return self._gui.is_key_pressed()
    
    def is_key_released(self):
        return self._gui.is_key_released()
    
    
def inference_from_microphone():

    # Audio recorder and classifier
    audio_clf = AudioClassifierWithGUI(
        SRC_WEIGHT_PATH, SRC_CLASSES_PATH, DST_AUDIO_FOLDER)

    # Start loop
    timer_printer = TimerPrinter(print_period=2.0)  # for print
    while not audio_clf.is_key_quit_pressed():
        timer_printer.print("Usage: keep pressing down 'R' to record audio")
        if audio_clf.is_key_pressed():
            audio_clf.record_audio_and_classifiy(shout_out_result=False)
        time.sleep(0.1)

if __name__=="__main__":
    inference_from_microphone()