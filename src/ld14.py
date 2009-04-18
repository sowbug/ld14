# Ludum Dare 14
# Copyright (c) 2009 Mike Tsao

from pygame.locals import *
import math
import os
import pygame
import random
import sys
import time

SCREEN_SIZE_X = 320
SCREEN_SIZE_Y = 480
ASSET_DIR = 'assets'

def load_image(name, colorkey=None):
  fullname = os.path.join(ASSET_DIR, name)
  try:
    image = pygame.image.load(fullname)
  except pygame.error, message:
    print 'Cannot load image:', fullname
    raise SystemExit, message
  image = image.convert()
  if colorkey is not None:
    if colorkey is - 1:
      colorkey = image.get_at((0, 0))
    image.set_colorkey(colorkey, RLEACCEL)
  return image, image.get_rect()

def load_sound(name):
  class NoneSound:
    def play(self): pass
  if not pygame.mixer or not pygame.mixer.get_init():
    return NoneSound()
  fullname = os.path.join(ASSET_DIR, name)
  try:
    sound = pygame.mixer.Sound(fullname)
  except pygame.error, message:
    print 'Cannot load sound:', fullname
    raise SystemExit, message
  return sound

class Tile(pygame.sprite.Sprite):
  def __init__(self, shape, color, top_left):
    pygame.sprite.Sprite.__init__(self)
    self.shape = shape
    self.color = color
    self.image, self.rect = load_image('tile_%d.png' % self.shape, - 1)
    self.image.set_colorkey((255, 0, 255))
    self.rect.topleft = top_left

  def update(self):
    pass

class Game(object):
  def __init__(self):
    self.clock = pygame.time.Clock()

    LEFT = 0
    TOP = 0
    RIGHT = SCREEN_SIZE_X
    BOTTOM = SCREEN_SIZE_Y
  
    pygame.init()
    self.screen = pygame.display.set_mode((RIGHT, BOTTOM))
    pygame.display.set_caption('Ludum Dare 14')
    pygame.mouse.set_visible(True)
  
    self.background = pygame.Surface(self.screen.get_size()).convert()
    self.background.fill((0xe0, 0xe0, 0xc0))
    
    self.grid_shapes = [[0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, ],
                        [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, ],
                        [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, ],
                        [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, ],
                        ]
    self.grid_colors = [[3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, ],
                        [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, ],
                        [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, ],
                        [3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, 3, 2, 1, 0, ]
                        ]
    self.grid_shapes = []
    self.grid_colors = []
    for row in range(0, 30):
      self.grid_shapes.append([])
      self.grid_colors.append([])
      if row > 10:
        continue
      for col in range(0, 20):
        self.grid_shapes[row].append(random.randint(0, 3))
        self.grid_colors[row].append(random.randint(0, 3))

    self.tile_sprites = pygame.sprite.Group([])
    for row in range(0, len(self.grid_shapes)):
      shape_row = self.grid_shapes[row]
      color_row = self.grid_colors[row]
      for col in range(0, len(shape_row)):
        shape = shape_row[col]
        color = color_row[col]
        self.tile_sprites.add(Tile(shape, color, (col * 16, row * 16)))

    self.screen.blit(self.background, (0, 0))
    pygame.display.flip()

  def draw_colors(self):
    RGB_TILE_COLOR = [(0xff, 0x00, 0x00),
                      (0x00, 0xff, 0x00),
                      (0x00, 0x00, 0xff),
                      (0xff, 0xff, 0x00),
                      ]
    for row in range(0, len(self.grid_colors)):
      color_row = self.grid_colors[row]      
      for col in range(0, len(color_row)):
        color = color_row[col]
        if color >= 0:
          self.screen.fill(RGB_TILE_COLOR[color],
                           pygame.Rect((col * 16, row * 16), (16, 16)))
    
  def run(self):
    while True:
      self.clock.tick(60)
  
      for event in pygame.event.get():
        if event.type == QUIT:
          return
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
          return
  
      self.tile_sprites.update()
    
      self.screen.blit(self.background, (0, 0))
      self.draw_colors()
      self.tile_sprites.draw(self.screen)
      pygame.display.flip()

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
