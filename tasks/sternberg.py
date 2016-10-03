import sys
import random
import time
import pandas as pd
import pygame

from pygame.locals import *
from itertools import product
from utils import display


class Sternberg(object):
    def __init__(self, screen, background, blocks=2):
        # Get the pygame display window
        self.screen = screen
        self.background = background

        # Sets font and font size
        self.font = pygame.font.SysFont("arial", 30)
        self.stim_font = pygame.font.SysFont("arial", 50)

        # Get screen info
        self.screen_x = self.screen.get_width()
        self.screen_y = self.screen.get_height()

        # Fill background
        self.background.fill((255, 255, 255))
        pygame.display.set_caption("Sternberg Task")
        pygame.mouse.set_visible(0)

        # Experiment options
        # Timings are taken from Sternberg (1966)
        # Block sizes are taken from Martins (2012)
        self.num_blocks = blocks
        self.stim_duration = 1200
        self.between_stim_duration = 250
        self.probe_warn_duration = 2000
        self.probe_duration = 2500
        self.feedback_duration = 1000
        self.ITI = 750
        self.stim_set = range(10)
        self.set_size = (2, 6)
        self.probe_type = ("present", "absent")

        # Create condition combinations
        self.combinations = list(product(self.set_size, self.probe_type))

        # Create practice trials
        # This gives 24 practice trials
        # TODO add the ability to manually set the number of trials
        self.practice_combinations = self.combinations * 6
        random.shuffle(self.practice_combinations)
        self.practice_trials = self.create_trials(self.practice_combinations)

        # Create main trial blocks
        self.blocks = []  # List will contain a dataframe for each block

        for i in range(self.num_blocks):
            # This creates 48 trials per block
            # TODO add the ability to manually set the number of trials
            block_combinations = self.combinations * 12
            random.shuffle(block_combinations)

            block = self.create_trials(block_combinations)
            block['block'] = str(i+1)  # Store the block number
            self.blocks.append(block)

    def create_trials(self, combinations):
        df = pd.DataFrame(combinations, columns=("setSize", "probeType"))

        for i, r in df.iterrows():
            # Store the current used set
            used_set = random.sample(self.stim_set, r['setSize'])
            unused_set = list(set(self.stim_set) - set(used_set))

            df.set_value(i, 'set', ''.join(str(x) for x in used_set))

            # Store the target probe number
            # Probe will be from/in the set 50% of the time (probe present)
            if r['probeType'] == "present":
                df.set_value(i, 'probe', str(random.choice(used_set)))
            else:
                df.set_value(i, 'probe', str(random.choice(unused_set)))

            # Store blank columns to be used later
            df['trialNum'] = ''
            df['block'] = ''
            df['response'] = ''
            df['RT'] = ''
            df['correct'] = ''

            # Rearrange the dataframe
            columns = ['trialNum', 'block', 'setSize', 'probeType', 'set',
                       'probe', 'response', 'RT', 'correct']
            df = df[columns]

        return df

    def display_trial(self, df, i, r):
        # Clear screen
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

        # Display number sequence
        self.display_sequence(r['set'])

        # Display probe warning/question
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "Was the following number in"
                                             " the original sequence?",
                     "center", "center")
        pygame.display.flip()

        start_time = int(round(time.time() * 1000))
        while int(round(time.time() * 1000)) - start_time < self.probe_warn_duration:
            pass

        # Display blank screen
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

        start_time = int(round(time.time() * 1000))
        while int(round(time.time() * 1000)) - start_time < self.between_stim_duration:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

        # Display probe
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.stim_font, r['probe'],
                     "center", "center", (0, 0, 255))
        display.text(self.screen, self.stim_font, "(yes)",
                     200, self.screen_y/2 + 200)
        display.text(self.screen, self.stim_font, "(no)",
                     self.screen_x - 200, self.screen_y/2 + 200)
        pygame.display.flip()

        start_time = int(round(time.time() * 1000))

        # clear the event queue before checking for responses
        pygame.event.clear()
        wait_response = True
        while wait_response:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_LEFT:
                    df.set_value(i, "response", "present")
                    wait_response = False
                elif event.type == KEYDOWN and event.key == K_RIGHT:
                    df.set_value(i, "response", "absent")
                    wait_response = False
                elif event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

            end_time = int(round(time.time() * 1000))

            # if time limit has been reached, consider it a missed trial
            if end_time - start_time >= self.probe_duration:
                wait_response = False

        # Store RT
        rt = int(round(time.time() * 1000)) - start_time
        df.set_value(i, "RT", rt)

        # Display blank screen
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

        start_time = int(round(time.time() * 1000))
        while int(round(time.time() * 1000)) - start_time < self.between_stim_duration:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

        # Display feedback
        self.screen.blit(self.background, (0, 0))

        if df["probeType"][i] == df["response"][i]:
            df.set_value(i, "correct", 1)
            display.text(self.screen, self.font, "correct",
                         "center", "center", (0, 255, 0))
        else:
            df.set_value(i, "correct", 0)
            display.text(self.screen, self.font, "incorrect",
                         "center", "center", (255, 0, 0))

        pygame.display.flip()

        start_time = int(round(time.time() * 1000))
        while int(round(time.time() * 1000)) - start_time < self.feedback_duration:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

        # Display blank screen (ITI)
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

        start_time = int(round(time.time() * 1000))
        while int(round(time.time() * 1000)) - start_time < self.ITI:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

    def display_sequence(self, sequence):
        for i, number in enumerate(sequence):
            # Display number
            self.screen.blit(self.background, (0, 0))
            display.text(self.screen, self.stim_font, number,
                         "center", "center")
            pygame.display.flip()

            start_time = int(round(time.time() * 1000))
            while int(round(time.time() * 1000)) - start_time < self.stim_duration:
                for event in pygame.event.get():
                    if event.type == KEYDOWN and event.key == K_F12:
                        sys.exit(0)

            # Display blank screen
            self.screen.blit(self.background, (0, 0))
            pygame.display.flip()

            start_time = int(round(time.time() * 1000))
            while int(round(time.time() * 1000)) - start_time < self.between_stim_duration:
                for event in pygame.event.get():
                    if event.type == KEYDOWN and event.key == K_F12:
                        sys.exit(0)

    def run(self):
        # Instructions screen
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font,
                     "You will see a sequence of numbers. "
                     "Try your best to memorize them",
                     100, 100)

        display.text(self.screen, self.font,
                     "You will then be shown a single test number", 100, 200)

        display.text(self.screen, self.font,
                     "If this number was in the original sequence, "
                     "press the LEFT arrow",
                     100, 400)

        display.text(self.screen, self.font,
                     "If this number was NOT in the original sequence, "
                     "press the RIGHT arrow",
                     100, 500)

        display.text(self.screen, self.font,
                     "Try to do this as quickly, "
                     "and as accurately, as possible",
                     100, 600)

        display.space_text(self.screen, self.font, "center", 800)

        pygame.display.flip()

        instruction_screen = True
        while instruction_screen:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_SPACE:
                    instruction_screen = False
                elif event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

        # Practice ready screen
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font,
                     "We will begin with some practice trials...",
                     "center", "center")

        display.space_text(self.screen, self.font,
                           "center", self.screen_y/2 + 100)

        pygame.display.flip()

        practice_ready_screen = True
        while practice_ready_screen:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_SPACE:
                    practice_ready_screen = False
                elif event.type == KEYDOWN and event.key == K_F12:
                    sys.exit(0)

        # Practice trials
        for i, r in self.practice_trials.iterrows():
            self.display_trial(self.practice_trials, i, r)

        print self.practice_trials

        # Main trials ready screen

        # Main trials

        # End screen
        self.screen.blit(self.background, (0, 0))
        display.text(self.screen, self.font, "End of task", "center", "center")
        display.space_text(self.screen, self.font,
                           "center", (self.screen_y / 2) + 100)
        pygame.display.flip()

        end_screen = True
        while end_screen:
            for event in pygame.event.get():
                if event.type == KEYDOWN and event.key == K_SPACE:
                    end_screen = False

        # Concatenate blocks and add trial numbers
        all_data = pd.concat(self.blocks)
        all_data['trialNum'] = range(1, len(all_data)+1)

        print "- Sternberg Task complete"

        return all_data
