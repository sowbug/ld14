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
TILE_SIZE = 16
CLOCK_HEIGHT = 8

SHAPE_COUNT = 4
COLOR_COUNT = 4
TRANSPARENCY_KEY_COLOR = (255, 0, 255)

SLOT_COUNT = 4
SLOT_SIZE = 64
SLOT_MARGIN = 4
SLOT_LEFT_MARGIN = (SCREEN_SIZE_X - (SLOT_COUNT * SLOT_SIZE + 
                                    (SLOT_COUNT - 1) * SLOT_MARGIN)) / 2

TILE_COLS = SCREEN_SIZE_X / TILE_SIZE
TILE_ROWS = (SCREEN_SIZE_Y - 80) / TILE_SIZE
DASHBOARD_START = TILE_ROWS * TILE_SIZE
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
    self.image.set_colorkey(TRANSPARENCY_KEY_COLOR)
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
  FPS = 15

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
    for shape in range(0, SHAPE_COUNT):
        img, rect = load_image('bigtile_%d.png' % shape, - 1)
        img.set_colorkey(TRANSPARENCY_KEY_COLOR)
        self.tile_images.append(img)
    self.slot_image, self.slot_rect = load_image('slot.png', - 1)
    self.slot_image.set_colorkey(TRANSPARENCY_KEY_COLOR)
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

    if pygame.font:
      self.font = pygame.font.Font(None, 20)
    self.banner = None
    self.banner_countdown = 0
    self.banner_alpha = 0

    self.enqueued_banner_messages = []
    self.enqueue_banner_message("Welcome to Sowbug's Ludum Dare #14 entry")
    self.enqueue_banner_message("Click tiles to add them to the slots")
    self.enqueue_banner_message("Remove tiles by grouping them in the slots")
    self.enqueue_banner_message("Four of one color are a group")
    self.enqueue_banner_message("So are four of one shape")
    self.enqueue_banner_message("Don't let the tiles reach the bottom!")

    self.screen.blit(self.background, (0, 0))
    pygame.display.flip()

  def generate_banner(self, text):
    if self.font:
      self.banner = pygame.Surface((SCREEN_SIZE_X,
                                    self.font.get_height() + 16))
      self.banner.fill((0, 0, 192))
      self.banner.set_alpha(self.banner_alpha)
      text = self.font.render(text, 1, (255, 255, 0))
      textpos = text.get_rect(centerx=self.banner.get_width() / 2)
      textpos.top = 8
      self.banner.blit(text, textpos)

  def enqueue_banner_message(self, text):
    self.enqueued_banner_messages.append(text)

  def tick_banner(self, msec_since_last):
    if not self.banner:
      try:
        message = self.enqueued_banner_messages.pop(0)
        if message:
          self.generate_banner(message)
          self.banner_countdown = 4000
      except IndexError:
        pass
      return
    self.banner_countdown -= msec_since_last
    if self.banner_countdown <= 0:
      self.banner = None
    else:
      if self.banner_countdown < 1000:
        self.banner_alpha = int(255 * float(self.banner_countdown) / 1000.0)
      else:
        self.banner_alpha = 255
      self.banner.set_alpha(self.banner_alpha)

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
      # this could leak tiles but we don't currently use it in the way
      # that would leak (replacing a non-scrolled row)
      self.grid_tiles[row] = []
    else:
      self.grid_tiles.append([])
    if should_fill:
      for col in range(0, TILE_COLS):
        shape = random.randint(0, SHAPE_COUNT - 1)
        color = random.randint(0, COLOR_COUNT - 1)
        self.grid_shapes[row].append(shape)
        self.grid_colors[row].append(color)
        tile = Tile(shape, color, (col * TILE_SIZE, row * TILE_SIZE))
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
                           pygame.Rect((col * TILE_SIZE, row * TILE_SIZE),
                                       (TILE_SIZE, TILE_SIZE)))

  def get_rowcol_from_pos(self, pos):
    return pos[1] / TILE_SIZE, pos[0] / TILE_SIZE

  def adjust_slot_pointer(self):
    for i in range(0, SLOT_COUNT):
      if self.slot_selection[i] == (-1, - 1):
        self.current_slot = i
        return
    self.handle_slot_completion()

  def unselect_slot(self, index):
    (row, col) = self.slot_selection[index]
    self.slot_selection[index] = (-1, - 1)
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
      if self.grid_shapes[row][col] == - 1:
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
        if last_row[col] != - 1:
          print 'you lose'
          sys.exit()
    for row in range(TILE_ROWS - 1, 0, - 1):
      self.grid_shapes[row] = self.grid_shapes[row - 1]
      self.grid_colors[row] = self.grid_colors[row - 1]
      self.grid_tiles[row] = self.grid_tiles[row - 1]
      for tile in self.grid_tiles[row]:
        if tile:
          tile.rect.top += TILE_SIZE 
    self.create_row(0)
    for i in range(0, SLOT_COUNT):
      if self.slot_selection[i][0] >= 0:
        self.slot_selection[i] = (self.slot_selection[i][0] + 1,
                                  self.slot_selection[i][1])

  def handle_mouseup(self, pos):
    tile_row, tile_col = self.get_rowcol_from_pos(pos)
    self.select_tile(tile_row, tile_col)

  def remove_tile(self, row, col):
    self.grid_shapes[row][col] = - 1
    self.grid_colors[row][col] = - 1
    tile = self.grid_tiles[row][col]
    self.grid_tiles[row][col] = None
    self.tile_sprites.remove(tile)
    del tile

  def handle_slot_completion(self):
    shapes_same = True
    colors_same = True
    last_shape = - 1
    last_color = - 1
    for i in range(0, SLOT_COUNT):
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
    if shapes_same or colors_same:
      for i in range(0, SLOT_COUNT):
        row, col = self.slot_selection[i]
        self.remove_tile(row, col)
    self.clear_slots()
    
  def clear_slots(self):
    if hasattr(self, 'slot_selection'):
      for i in range(0, SLOT_COUNT):
        row, col = self.slot_selection[i]
        if self.grid_tiles[row][col]:
          self.grid_tiles[row][col].selected = False
    self.slot_selection = [(-1, - 1), (-1, - 1), (-1, - 1), (-1, - 1), ]
    self.adjust_slot_pointer()

  def draw_slots(self):
    for i in range(0, SLOT_COUNT):
      x = i * (SLOT_SIZE + SLOT_MARGIN) + SLOT_LEFT_MARGIN
      y = DASHBOARD_START + SLOT_MARGIN
      row, col = self.slot_selection[i]
      if row >= 0 and col >= 0:      
        shape = self.grid_shapes[row][col]
        color = self.grid_colors[row][col]
        self.screen.fill(Game.RGB_TILE_COLOR[color],
                         pygame.Rect((x, y), (64, 64)))
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
    self.screen.fill(CLOCK_COLOR,
                      pygame.Rect(0,
                                  DASHBOARD_START + SLOT_SIZE + SLOT_MARGIN * 2,
                     int(remaining * SCREEN_SIZE_X), CLOCK_HEIGHT))

  def draw_floating_text(self):
    if self.banner:
      self.screen.blit(self.banner, (0, 300))
      
  def run(self):
    while True:
      elapsed = self.clock.tick(Game.FPS)
      self.wall_clock_msec -= elapsed
      if self.wall_clock_msec <= 0:
        self.advance_wall() 
        self.wall_clock_msec = self.wall_row_duration_msec
      self.update_pulse_color(Game.FPS)
      self.tick_banner(elapsed)

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
      self.draw_floating_text()
      pygame.display.flip()

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
