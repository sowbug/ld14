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

TILE_COLS = SCREEN_SIZE_X / 16
TILE_ROWS = (SCREEN_SIZE_Y - 80) / 16
DASHBOARD_START = TILE_ROWS * 16
CLOCK_COLOR = (255, 128, 0)
BACKGROUND_COLOR = (0xe0, 0xe0, 0xc0)
DASHBOARD_COLOR = (0xe0, 0xe0, 0xff)

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
    self.selected = False

  def update(self):
    pass

class Game(object):
  RGB_TILE_COLOR = [(0xff, 0x00, 0x00),
                    (0x00, 0xff, 0x00),
                    (0x00, 0x00, 0xff),
                    (0xff, 0xff, 0x00),
                    ]

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
    self.background.fill(BACKGROUND_COLOR,
                         pygame.Rect(0, 0, SCREEN_SIZE_X, DASHBOARD_START))
    self.background.fill(DASHBOARD_COLOR,
                         pygame.Rect(0, DASHBOARD_START, SCREEN_SIZE_X,
                                     SCREEN_SIZE_Y - DASHBOARD_START))
    
    self.pulse_color_dx = 0
    self.pulse_color = 0.75
    
    self.wall_row_duration_msec = 5000
    self.wall_clock_msec = self.wall_row_duration_msec

    self.tile_images = []
    for shape in range(0, 4):
        img, rect = load_image('bigtile_%d.png' % shape, - 1)
        img.set_colorkey((255, 0, 255))
        self.tile_images.append(img)
    self.slot_image, self.slot_rect = load_image('slot.png', - 1)
    self.slot_image.set_colorkey((255, 0, 255))
    self.clear_slots()

    self.tile_sprites = pygame.sprite.Group([])
    self.grid_shapes = []
    self.grid_colors = []
    self.grid_tiles = []
    for row in range(0, TILE_ROWS):
      self.grid_shapes.append([])
      self.grid_colors.append([])
      self.grid_tiles.append([])
      self.create_row(row, row < 5) # level 1, fill in just 5 rows at top

    self.screen.blit(self.background, (0, 0))
    pygame.display.flip()

  def create_row(self, row, should_fill=True):
    if len(self.grid_shapes) > row:
      self.grid_shapes[row] = []
    else:
      self.grid_shapes.append([])
    if len(self.grid_colors) > row:
      self.grid_colors[row] = []
    else:
      self.grid_colors.append([])
    if len(self.grid_tiles) > row:
      self.grid_tiles[row] = [] # this leaks tiles but we don't currently use it
      print 'WARNING LEAK'
    else:
      self.grid_tiles.append([])
    if should_fill:
      for col in range(0, TILE_COLS):
        shape = random.randint(0, 3)
        color = random.randint(0, 3)
        self.grid_shapes[row].append(shape)
        self.grid_colors[row].append(color)
        tile = Tile(shape, color, (col * 16, row * 16))
        self.tile_sprites.add(tile)
        self.grid_tiles[row].append(tile)

  def draw_colors(self):
    for row in range(0, len(self.grid_colors)):
      color_row = self.grid_colors[row]      
      for col in range(0, len(color_row)):
        color = color_row[col]
        if color >= 0:
          if self.grid_tiles[row][col].selected:
            rgb_color = Game.RGB_TILE_COLOR[color]
            rgb_color = (rgb_color[0] * self.pulse_color,
                         rgb_color[1] * self.pulse_color,
                         rgb_color[2] * self.pulse_color) 
          else:
            rgb_color = Game.RGB_TILE_COLOR[color]
          self.screen.fill(rgb_color,
                           pygame.Rect((col * 16, row * 16), (16, 16)))

  def get_rowcol_from_pos(self, pos):
    return pos[1] / 16, pos[0] / 16

  def adjust_slot_pointer(self):
    for i in range(0, 4):
      if self.slot_selection[i] == (-1, -1):
        self.current_slot = i
        return
    self.handle_slot_completion()

  def unselect_slot(self, index):
    (row, col) = self.slot_selection[index]
    self.slot_selection[index] = (-1, -1)
    self.grid_tiles[row][col].selected = False
    self.adjust_slot_pointer()

  def select_tile(self, row, col):
    selected = True
    
    # already selected this tile in prior slot?
    for i in range(0, self.current_slot):
      (t_row, t_col) = self.slot_selection[i]
      if t_row == row and t_col == col:
        self.unselect_slot(i)
        selected = False
        break

    # tried to select an empty tile?
    if selected:
      if self.grid_shapes[row][col] == -1:
        selected = False

    if selected:
      self.slot_selection[self.current_slot] = (row, col)
      self.grid_tiles[row][col].selected = True
      self.adjust_slot_pointer()
    self.draw_slots()

  def advance_wall(self):
    # This is LD so I'm doing the dumb expensive scroll
    last_row = self.grid_shapes[TILE_ROWS - 2] # -1 x 2 because it's pre-scroll
    if len(last_row) > 0:
      for col in range(0, TILE_COLS):
        print col
        if last_row[col] != -1:
          print 'you lose'
          sys.exit()
    for row in range(TILE_ROWS - 1, 0, -1):
      self.grid_shapes[row] = self.grid_shapes[row - 1]
      self.grid_colors[row] = self.grid_colors[row - 1]
      self.grid_tiles[row] = self.grid_tiles[row - 1]
      for tile in self.grid_tiles[row]:
        if tile:
          tile.rect.top += 16 
    self.create_row(0)
    for i in range(0, 4):
      if self.slot_selection[i][0] >= 0:
        self.slot_selection[i] = (self.slot_selection[i][0] + 1,
                                  self.slot_selection[i][1])

  def handle_mouseup(self, pos):
    tile_row, tile_col = self.get_rowcol_from_pos(pos)
    self.select_tile(tile_row, tile_col)

  def remove_tile(self, row, col):
    self.grid_shapes[row][col] = -1
    self.grid_colors[row][col] = -1
    tile = self.grid_tiles[row][col]
    self.grid_tiles[row][col] = None
    self.tile_sprites.remove(tile)
    del tile

  def handle_slot_completion(self):
    shapes_same = True
    colors_same = True
    last_shape = -1
    last_color = -1
    for i in range(0, 4):
      row, col = self.slot_selection[i]
      shape = self.grid_shapes[row][col]
      color = self.grid_colors[row][col]
      if last_shape >= 0:
        if shape != last_shape:
          shapes_same = False
      last_shape = shape
      if last_color >= 0:
        if color != last_color:
          colors_same = False
      last_color = color
    print 'Shapes same: %s' % shapes_same
    print 'Colors same: %s' % colors_same
    if shapes_same or colors_same:
      for i in range(0, 4):
        row, col = self.slot_selection[i]
        self.remove_tile(row, col)
    self.clear_slots()
    
  def clear_slots(self):
    if hasattr(self, 'slot_selection'):
      for i in range(0, 4):
        row, col = self.slot_selection[i]
        if self.grid_tiles[row][col]:
          self.grid_tiles[row][col].selected = False
    self.slot_selection = [(-1, -1), (-1, -1), (-1, -1), (-1, -1), ]
    self.adjust_slot_pointer()

  def draw_slots(self):
    for i in range(0, 4):
      x = i * (64 + 4) + 24
      y = DASHBOARD_START
      row, col = self.slot_selection[i]
      if row >= 0 and col >= 0:      
        shape = self.grid_shapes[row][col]
        color = self.grid_colors[row][col]
        print 'tile at %d %d is %d %d' % (row, col, shape, color)
        self.screen.fill(Game.RGB_TILE_COLOR[color], pygame.Rect((x, y), (64, 64)))
        self.screen.blit(self.tile_images[shape], (x, y))
      self.screen.blit(self.slot_image, (x, y))

  def update_pulse_color(self, fps):
    if self.pulse_color_dx == 0:
      self.pulse_color_dx = float(2.0 / 1.0) / fps
    self.pulse_color += self.pulse_color_dx
    if self.pulse_color >= 1.0:
      self.pulse_color = 1.0
      self.pulse_color_dx = - self.pulse_color_dx
    if self.pulse_color <= 0.5:
      self.pulse_color = 0.5
      self.pulse_color_dx = - self.pulse_color_dx

  def draw_wall_clock(self):
    remaining = float(self.wall_clock_msec) / float(self.wall_row_duration_msec)
    self.screen.fill(CLOCK_COLOR, pygame.Rect(0, DASHBOARD_START + 68,
                     int(remaining * SCREEN_SIZE_X), 16))

  def run(self):
    while True:
      FPS = 15
      elapsed = self.clock.tick(FPS)
      self.wall_clock_msec -= elapsed
      if self.wall_clock_msec <= 0:
        self.advance_wall() 
        self.wall_clock_msec = self.wall_row_duration_msec
      self.update_pulse_color(FPS)

      for event in pygame.event.get():
        if event.type == QUIT:
          return
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
          return
        elif event.type == MOUSEBUTTONUP:
          self.handle_mouseup(event.pos)
        elif event.type == MOUSEMOTION:
          pass

      self.tile_sprites.update()
    
      self.screen.blit(self.background, (0, 0))
      self.draw_colors()
      self.tile_sprites.draw(self.screen)
      self.draw_slots()
      self.draw_wall_clock()
      pygame.display.flip()

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
