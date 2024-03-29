# Flood of Air
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
TILE_SIZE = 32
CLOCK_HEIGHT = 7

TILE_SYMBOL = ['A', 'B', 'C', 'D', 'E', 'X']
RGB_TILE_COLOR = [(0xff, 0x00, 0x00),
                  (0x00, 0xf0, 0x00),
                  (0x80, 0x80, 0xff),
                  (0xf0, 0xf0, 0x00),
                  ]
RGB_TILE_END_COLOR = [(0xcf, 0x00, 0x00),
                      (0x00, 0xcf, 0x00),
                      (0x6f, 0x6f, 0xcf),
                      (0xaf, 0xaf, 0x00),
                      ]

SHAPE_COUNT = len(TILE_SYMBOL)
SPECIAL_SHAPE = SHAPE_COUNT - 1
COLOR_COUNT = len(RGB_TILE_COLOR)
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
BACKGROUND_COLOR = (0xff, 0xff, 0xe0)
BACKGROUND_END_COLOR = (0xe8, 0xe8, 0xd8)
DASHBOARD_COLOR = (0xe0, 0xe0, 0xff)
DASHBOARD_END_COLOR = (0xc8, 0xc8, 0xf8)
SCORE_COLOR = (0, 128, 0)
GAME_OVER_COLOR = (48, 48, 48)
SPECIAL_TILE_COLOR = (128, 128, 128)

TILE_COLOR = (16, 16, 16)
TILE_BACKGROUND_COLOR = DASHBOARD_COLOR
TILE_BACKGROUND_END_COLOR = (0xa8, 0xa8, 0xc8)
TILE_BACKGROUND_MARGIN = 5
SLOT_BACKGROUND_COLOR = DASHBOARD_COLOR
SLOT_BACKGROUND_END_COLOR = (0xa0, 0xa0, 0xc0)
SLOT_BACKGROUND_MARGIN = 16
BANNER_ALPHA = 192

def get_font(size):
  return pygame.font.Font('fonts/Surface_Medium.otf', size)
  
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
  def __init__(self, image, shape, color, top_left, parent_group):
    pygame.sprite.Sprite.__init__(self)
    self.parent_group = parent_group
    self.shape = shape
    self.color = color
    self.image = image
    self.original = self.image
    self.rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
    self.reposition(top_left)
    self.selected = False
    self.falling = False

  def apply_vertical_offset(self, offset):
    if not self.falling:
      self.rect.top = self.original_top + offset

  def reposition(self, top_left):
    self.rect.topleft = top_left
    self.original_top = top_left[1]

  def start_fall(self):
    self.falling = True
    self.current_angle = 0
    self.dx = 1.0 + random.random()
    self.rot_dx = 1.0 + random.random() * 5.0
    if self.rect.left > SCREEN_SIZE_X / 2:
      self.dx = - self.dx
      self.rot_dx = - self.rot_dx
    self.dy = - 0.05

  def update(self):
    if not self.falling:
      return
    self.dy += 0.65
    self.rect.left += self.dx
    self.rect.top += self.dy
    rotate = pygame.transform.rotate
    self.current_angle += self.rot_dx
    self.image = rotate(self.original, self.current_angle)
    if self.rect.top > SCREEN_SIZE_Y:
      self.parent_group.remove(self)      

class Score(pygame.sprite.Sprite):
  def __init__(self, score, top_left, parent_group):
    self.parent_group = parent_group
    pygame.sprite.Sprite.__init__(self)
    font = get_font(72)
    text = font.render('%d' % score, 0, SCORE_COLOR)
    textpos = text.get_rect()
    self.image = pygame.Surface((textpos.bottomright))
    self.image.set_colorkey(TRANSPARENCY_KEY_COLOR)
    self.image.fill(TRANSPARENCY_KEY_COLOR)
    self.image.blit(text, textpos)
    self.original = self.image
    self.rect = textpos
    self.rect.topleft = top_left
    self.current_angle = 0
    self.dx = 1.0 + random.random()
    self.rot_dx = 1.0 + random.random()
    if self.rect.left > SCREEN_SIZE_X / 2:
      self.dx = - self.dx
      self.rot_dx = - self.rot_dx
    self.dy = - 5.0

  def update(self):
    self.dy += 0.4
    self.rect.left += self.dx
    self.rect.top += self.dy
    rotate = pygame.transform.rotate
    self.current_angle += self.rot_dx
    self.image = rotate(self.original, self.current_angle)
    if self.rect.top > SCREEN_SIZE_Y:
      self.parent_group.remove(self)      

class Game(object):
  FPS = 30

  def __init__(self):
    self.clock = pygame.time.Clock()

    LEFT = 0
    TOP = 0
    RIGHT = SCREEN_SIZE_X
    BOTTOM = SCREEN_SIZE_Y

    pygame.init()
    self.screen = pygame.display.set_mode((RIGHT, BOTTOM))
    pygame.display.set_caption('Ludum Dare 14: Flood of Air')
    pygame.mouse.set_visible(True)
  
    self.background = pygame.Surface(self.screen.get_size()).convert()
    self.do_gradient(self.background, pygame.Rect(0, 0, SCREEN_SIZE_X, DASHBOARD_START),
                     BACKGROUND_COLOR, BACKGROUND_COLOR)
    self.do_gradient(self.background, pygame.Rect(0, DASHBOARD_START, SCREEN_SIZE_X,
                                                  SCREEN_SIZE_Y - DASHBOARD_START),
                                                  DASHBOARD_COLOR, DASHBOARD_END_COLOR)

    self.prerender()
    
    self.pulse_color_dx = 0
    self.pulse_color = 0.75
    self.special_color_dx = 0
    self.special_color = 0.75

    self.enqueued_banner_messages = []
    self.enqueue_banner_message("Click tiles to add them to the slots")
    self.enqueue_banner_message("Remove tiles by grouping them in the slots")
    self.enqueue_banner_message("A group is four of a color or shape")
    self.enqueue_banner_message("Don't let the tiles reach the bottom!")

    self.level = 0
    self.set_level(1)
    self.update_wall_row_duration()
    self.update_level_duration()
    self.wall_clock_msec = self.wall_row_duration_msec
    self.level_clock_msec = self.level_duration_msec

    self.vertical_tile_offset = 0
    
    self.slot_completion_countdown = 0
    
    self.score = 0
    
    self.generate_tile_images()

    self.slot_image, self.slot_rect = load_image('slot.png', - 1)
    self.slot_image.set_colorkey(TRANSPARENCY_KEY_COLOR)
    self.clear_slots()

    self.tile_sprites = pygame.sprite.Group([])
    self.score_sprites = pygame.sprite.Group([])
    self.grid_shapes = []
    self.grid_colors = []
    self.grid_tiles = []
    for row in range(0, TILE_ROWS):
      self.grid_shapes.append([])
      self.grid_colors.append([])
      self.grid_tiles.append([])
      self.create_row(row, row < 5) # level 1, fill in just 5 rows at top

    if pygame.font:
      self.font = get_font(20)
    self.banner = None
    self.banner_countdown = 0
    self.banner_alpha = 0
    
    self.wall_advancement_sound = load_sound('wall_advancement.wav')
    self.select_tile_sound = load_sound('select_tile.wav')
    self.unselect_tile_sound = load_sound('unselect_tile.wav')
    self.group_good_sound = load_sound('group_good.wav')
    self.group_great_sound = load_sound('group_great.wav')
    self.group_bad_sound = load_sound('group_bad.wav')
    self.game_over_sound = load_sound('game_over.wav')
    self.special_tile_pickup = load_sound('special_tile_pickup.wav') 

    self.game_over = False
    self.special_hint_count = 0

    self.screen.blit(self.background, (0, 0))
    pygame.display.flip()

  def do_gradient(self, image, rect, bg_color, bg_gradient):
    #image.fill(bg_color, rect)
    #return
    x1 = rect.left
    x2 = rect.right
    a, b = bg_color, bg_gradient
    y1 = rect.top
    y2 = rect.bottom
    h = rect.height
    rate = (float((b[0] - a[0]) / h), (float(b[1] - a[1]) / h),
            (float(b[2] - a[2]) / h))
    for line in range(y1, y2):
      offset = line - y1
      color = (min(max(a[0] + (rate[0] * offset), 0), 255),
               min(max(a[1] + (rate[1] * offset), 0), 255),
               min(max(a[2] + (rate[2] * offset), 0), 255))
      pygame.draw.line(image, color, (x1, line), (x2, line))

  def generate_tile_images(self):
    self.tile_images = []
    font = get_font(36)
    for shape in range(0, SHAPE_COUNT):
      image = pygame.Surface((SLOT_SIZE, SLOT_SIZE))
      image.set_colorkey(TRANSPARENCY_KEY_COLOR)
      image.fill(TRANSPARENCY_KEY_COLOR)
      self.do_gradient(image,
                       pygame.Rect(SLOT_BACKGROUND_MARGIN,
                                   SLOT_BACKGROUND_MARGIN,
                                   SLOT_SIZE - SLOT_BACKGROUND_MARGIN * 2,
                                   SLOT_SIZE - SLOT_BACKGROUND_MARGIN * 2),
                                   SLOT_BACKGROUND_COLOR, SLOT_BACKGROUND_END_COLOR)
      text = font.render(TILE_SYMBOL[shape], 1, TILE_COLOR)
      textpos = text.get_rect(centerx=SLOT_SIZE / 2)
      textpos.top = 1 + (SLOT_SIZE - font.get_height()) / 2
      image.blit(text, textpos)
      self.tile_images.append(image)

    self.small_tile_images = []
    font = get_font(20)
    for shape in range(0, SHAPE_COUNT):
      image = pygame.Surface((TILE_SIZE, TILE_SIZE))
      image.set_colorkey(TRANSPARENCY_KEY_COLOR)
      image.fill(TRANSPARENCY_KEY_COLOR)
      if shape == SPECIAL_SHAPE:
        margin = TILE_BACKGROUND_MARGIN + 2
      else:
        margin = TILE_BACKGROUND_MARGIN
      self.do_gradient(image,
                       pygame.Rect(margin, margin,
                                   TILE_SIZE - margin * 2, TILE_SIZE - margin * 2),
                                   TILE_BACKGROUND_COLOR, TILE_BACKGROUND_END_COLOR)
      text = font.render(TILE_SYMBOL[shape], 1, TILE_COLOR)
      textpos = text.get_rect(centerx=TILE_SIZE / 2)
      textpos.top = 1 + (TILE_SIZE - font.get_height()) / 2
      image.blit(text, textpos)
      self.small_tile_images.append(image)

  def set_level(self, new_level):
    if self.level != new_level:
      self.level = new_level
      self.enqueue_banner_message("Current Level: %d" % self.level)

  def get_wall_row_duration_msec(self):
    return max(5000, 15000 - pow(self.level, 1.4) * 1000)
  
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
        self.banner_alpha = int(BANNER_ALPHA * float(self.banner_countdown) / 1000.0)
      else:
        self.banner_alpha = BANNER_ALPHA
      self.banner.set_alpha(self.banner_alpha)

  def get_random_shape_index(self, allow_special=False):
    if allow_special:
      return random.randint(0, SHAPE_COUNT - 1)
    return random.randint(0, SHAPE_COUNT - 2)

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
        # The last shape is special. Early levels don't get it. 
        if self.level < 2:
          shape = self.get_random_shape_index()
        else:
          shape = self.get_random_shape_index(allow_special=True)
          # The last shape was picked. Go through with it according to a
          # probability that increases with the levels.
          if shape == SPECIAL_SHAPE:
            random_threshold = float(self.level) / 10.0
            if random_threshold < random.random():
              # Nope, change to regular shape
              shape = self.get_random_shape_index()

        # debug
        if False and random.random() > 0.8:
          shape = SPECIAL_SHAPE
        # debug
        
        color = random.randint(0, COLOR_COUNT - 1)
        self.grid_shapes[row].append(shape)
        self.grid_colors[row].append(color)
        tile = Tile(self.small_tile_images[shape],
                    shape, color, (col * TILE_SIZE, row * TILE_SIZE),
                    self.tile_sprites)
        self.tile_sprites.add(tile)
        self.grid_tiles[row].append(tile)

  def draw_colors(self):
    for row in range(0, len(self.grid_colors)):
      color_row = self.grid_colors[row]      
      shape_row = self.grid_shapes[row]      
      for col in range(0, len(color_row)):
        color = color_row[col]
        shape = shape_row[col]
        if color >= 0:
          use_prerendered = False
          if self.grid_tiles[row][col].selected:
            rgb_color = RGB_TILE_COLOR[color]
            rgb_color = (rgb_color[0] * self.pulse_color,
                         rgb_color[1] * self.pulse_color,
                         rgb_color[2] * self.pulse_color) 
            rgb_end_color = RGB_TILE_END_COLOR[color]
            rgb_end_color = (rgb_end_color[0] * self.pulse_color,
                             rgb_end_color[1] * self.pulse_color,
                             rgb_end_color[2] * self.pulse_color) 
          else:
            use_prerendered = True
          if shape == SPECIAL_SHAPE:
            use_prerendered = False
            rgb_color = SPECIAL_TILE_COLOR
            rgb_color = (rgb_color[0] * self.special_color,
                         rgb_color[1] * self.special_color,
                         rgb_color[2] * self.special_color)
            rgb_end_color = rgb_color 
          if self.game_over:
            use_prerendered = False
            rgb_color = GAME_OVER_COLOR
            rgb_end_color = GAME_OVER_COLOR
          rect = pygame.Rect((col * TILE_SIZE + 1, row * TILE_SIZE + 1),
                             (TILE_SIZE - 2, TILE_SIZE - 2))
          rect.top += self.vertical_tile_offset
          if use_prerendered:
            self.screen.blit(self.tile_prerenders[color], rect)
          else:
            # This uses a little too much CPU  
            if True:
              self.do_gradient(self.screen, rect, rgb_color, rgb_end_color)
            else:
              self.screen.fill(rgb_color, rect)

  def get_rowcol_from_pos(self, pos):
    x = pos[0]
    y = pos[1] - self.vertical_tile_offset
    return y / TILE_SIZE, x / TILE_SIZE

  def adjust_slot_pointer(self):
    for i in range(0, SLOT_COUNT):
      if self.slot_selection[i] == (-1, - 1):
        self.current_slot = i
        return
    self.current_slot = - 1
    self.slot_completion_countdown = 250

  def unselect_slot(self, index):
    (row, col) = self.slot_selection[index]
    if row >= 0:
      self.unselect_tile_sound.play()
      self.grid_tiles[row][col].selected = False
    self.slot_selection[index] = (-1, - 1)
    self.adjust_slot_pointer()

  def select_tile(self, row, col):
    selected = True

    if len(self.grid_shapes) - 1 < row:
      return
    if len(self.grid_shapes[row]) - 1 < col:
      return

    # already selected this tile in prior slot?
    for i in range(0, SLOT_COUNT):
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
      if self.grid_shapes[row][col] == SPECIAL_SHAPE:
        self.unselect_tile_sound.play()
        if self.special_hint_count < 3:
          self.special_hint_count += 1
          self.enqueue_banner_message('%s tiles are special!' % TILE_SYMBOL[SPECIAL_SHAPE])
          self.enqueue_banner_message('Remove their neighbors!')
        selected = False
      
    if selected:
      self.slot_selection[self.current_slot] = (row, col)
      self.grid_tiles[row][col].selected = True
      self.adjust_slot_pointer()
      self.select_tile_sound.play()
    self.draw_slots()

  def advance_wall(self):
    self.wall_advancement_sound.play()
    # This is LD so I'm doing the dumb expensive scroll rather than
    # some sort of interesting sliding view on the data
    last_row = self.grid_shapes[TILE_ROWS - 2] # -1 x 2 because it's pre-scroll
    last_row = self.grid_shapes[10] # REMOVE THIS
    if len(last_row) > 0:
      for col in range(0, TILE_COLS):
        if last_row[col] != - 1:
          self.enqueue_banner_message("GAME OVER")
          self.game_over = True
          self.game_over_sound.play()
    for row in range(TILE_ROWS - 1, 0, - 1):
      self.grid_shapes[row] = self.grid_shapes[row - 1]
      self.grid_colors[row] = self.grid_colors[row - 1]
      self.grid_tiles[row] = self.grid_tiles[row - 1]
      for tile in self.grid_tiles[row]:
        if tile:
          r = tile.rect
          r.top = tile.original_top + TILE_SIZE
          tile.reposition(r.topleft)
    self.create_row(0)
    for i in range(0, SLOT_COUNT):
      if self.slot_selection[i][0] >= 0:
        self.slot_selection[i] = (self.slot_selection[i][0] + 1,
                                  self.slot_selection[i][1])

  def get_slot_from_pos(self, pos):
    if pos[1] < DASHBOARD_START:
      return - 1
    if pos[0] < SLOT_LEFT_MARGIN or pos[0] > SCREEN_SIZE_X - SLOT_LEFT_MARGIN:
      return - 1
    return (pos[0] - SLOT_LEFT_MARGIN) / (SLOT_SIZE + SLOT_MARGIN)

  def handle_mouseup(self, pos):
    tile_row, tile_col = self.get_rowcol_from_pos(pos)
    if tile_row < TILE_ROWS:
      self.select_tile(tile_row, tile_col)
    slot_pos = self.get_slot_from_pos(pos)
    if slot_pos >= 0:
      self.unselect_slot(slot_pos)

  def safe_get_grid_shape(self, row, col):
    if len(self.grid_shapes) <= row:
      return - 1
    if len(self.grid_shapes[row]) <= col:
      return - 1
    return self.grid_shapes[row][col]
    
  def remove_tile(self, row, col):
    self.grid_shapes[row][col] = - 1
    self.grid_colors[row][col] = - 1
    tile = self.grid_tiles[row][col]
    self.grid_tiles[row][col] = None
    tile.start_fall()
    self.scan_for_special_tiles(row, col)

  def check_special_tile(self, row, col):
    if self.safe_get_grid_shape(row, col) != SPECIAL_SHAPE:
      return
    neighbors = []
    if row >= 1:
      neighbors.append(self.safe_get_grid_shape(row - 1, col))
    if row < TILE_ROWS - 1:
      neighbors.append(self.safe_get_grid_shape(row + 1, col))
    if col >= 1:
      neighbors.append(self.safe_get_grid_shape(row, col - 1))
    if col < TILE_COLS - 1:
      neighbors.append(self.safe_get_grid_shape(row, col + 1))
    for n in neighbors:
      if n != - 1 and n != SPECIAL_SHAPE:
        return
    self.remove_tile(row, col)
    self.special_tile_pickup.play()

  # Given that a tile was just removed, see whether the removal affects
  # a special tile, and handle if that's the case
  def scan_for_special_tiles(self, row, col):
    if row >= 1:
      self.check_special_tile(row - 1, col)
    if row < TILE_ROWS - 1:
      self.check_special_tile(row + 1, col)
    if col >= 1:
      self.check_special_tile(row, col - 1)
    if col < TILE_COLS - 1:
      self.check_special_tile(row, col + 1)

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
      temp_score = 0
      row_sum = 0
      col_sum = 0
      for i in range(0, SLOT_COUNT):
        row, col = self.slot_selection[i]
        self.remove_tile(row, col)
        row_sum += row
        col_sum += col
        temp_score = TILE_ROWS - row
        temp_score *= self.level
        if shapes_same and colors_same:
          temp_score *= 3
          self.group_great_sound.play()
        else:
          self.group_good_sound.play()
      self.score += temp_score
      position = (TILE_SIZE * col_sum / SLOT_COUNT,
                  TILE_SIZE * row_sum / SLOT_COUNT)
      self.float_score_bubble(temp_score, position)        
    else:
      self.group_bad_sound.play()
    self.clear_slots()

  def float_score_bubble(self, score, position):
    sprite = Score(score, position, self.score_sprites)
    self.score_sprites.add(sprite)

  def clear_slots(self):
    if hasattr(self, 'slot_selection'):
      for i in range(0, SLOT_COUNT):
        row, col = self.slot_selection[i]
        if self.grid_tiles[row][col]:
          self.grid_tiles[row][col].selected = False
    self.slot_selection = [(-1, - 1), (-1, - 1), (-1, - 1), (-1, - 1), ]
    self.adjust_slot_pointer()

  def prerender(self):
    self.slot_prerenders = []
    self.tile_prerenders = []
    for color in range(0, COLOR_COUNT):
      image = pygame.Surface((SLOT_SIZE, SLOT_SIZE))
      self.do_gradient(image,
                       pygame.Rect((0, 0), (SLOT_SIZE, SLOT_SIZE)),
                       RGB_TILE_COLOR[color], RGB_TILE_END_COLOR[color])
      self.slot_prerenders.append(image)

      image = pygame.Surface((TILE_SIZE, TILE_SIZE))
      self.do_gradient(image,
                       pygame.Rect((0, 0), (TILE_SIZE, TILE_SIZE)),
                       RGB_TILE_COLOR[color], RGB_TILE_END_COLOR[color])
      self.tile_prerenders.append(image)

  def draw_slots(self):
    for i in range(0, SLOT_COUNT):
      x = i * (SLOT_SIZE + SLOT_MARGIN) + SLOT_LEFT_MARGIN
      y = DASHBOARD_START + SLOT_MARGIN
      row, col = self.slot_selection[i]
      if row >= 0 and col >= 0:
        shape = self.grid_shapes[row][col]
        color = self.grid_colors[row][col]
        self.screen.blit(self.slot_prerenders[color],
                         pygame.Rect((x, y),
                                     (SLOT_SIZE, SLOT_SIZE)))
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

    if self.special_color_dx == 0:
      self.special_color_dx = float(1.0 / 1.0) / fps
    self.special_color += self.special_color_dx
    if self.special_color >= 1.0:
      self.special_color = 1.0
      self.special_color_dx = - self.special_color_dx
    if self.special_color <= 0.5:
      self.special_color = 0.5
      self.special_color_dx = - self.special_color_dx

  def draw_wall_clock(self):
    remaining = float(self.wall_clock_msec) / float(self.wall_row_duration_msec)
    self.screen.fill(CLOCK_COLOR,
                      pygame.Rect(0,
                                  DASHBOARD_START + SLOT_SIZE + SLOT_MARGIN * 2,
                     int(remaining * SCREEN_SIZE_X), CLOCK_HEIGHT))

  def draw_floating_text(self):
    if self.banner:
      self.screen.blit(self.banner,
                       (0, DASHBOARD_START - self.banner.get_height() - SLOT_MARGIN))

  def tick_vertical_tile_offset(self):
    remaining = float(self.wall_clock_msec) / float(self.wall_row_duration_msec)
    self.vertical_tile_offset = int((1.0 - remaining) * TILE_SIZE)

  def update_wall_row_duration(self):
    self.wall_row_duration_msec = self.get_wall_row_duration_msec()

  def update_level_duration(self):
    self.level_duration_msec = self.wall_row_duration_msec * 4

  def draw_score(self):
    font = get_font(18)
    text = font.render('Score: %06d' % self.score, 1, SCORE_COLOR)
    textpos = text.get_rect()
    textpos.bottomright = (SCREEN_SIZE_X, SCREEN_SIZE_Y)
    self.screen.blit(text, textpos)

  def run(self):
    while True:
      elapsed = self.clock.tick(Game.FPS)
      if not self.game_over:
        self.wall_clock_msec -= elapsed
        if self.wall_clock_msec <= 0:
          self.advance_wall()
          self.update_wall_row_duration()
          self.wall_clock_msec = self.wall_row_duration_msec
        self.tick_vertical_tile_offset()
        self.level_clock_msec -= elapsed
        if self.level_clock_msec <= 0:
          self.set_level(self.level + 1)
          self.update_level_duration()
          self.level_clock_msec = self.level_duration_msec
          
      self.update_pulse_color(Game.FPS)
      self.tick_banner(elapsed)
      if self.slot_completion_countdown > 0:
        self.slot_completion_countdown -= elapsed
        if self.slot_completion_countdown <= 0:
          self.slot_completion_countdown = 0
          self.handle_slot_completion()

      for event in pygame.event.get():
        if event.type == QUIT:
          return
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
          return
        elif event.type == MOUSEBUTTONUP:
          if self.slot_completion_countdown == 0 and not self.game_over:
            self.handle_mouseup(event.pos)

      self.tile_sprites.update()
      for tile in self.tile_sprites:
        tile.apply_vertical_offset(self.vertical_tile_offset)
      self.score_sprites.update()

      self.screen.blit(self.background, (0, 0))
      self.draw_colors()
      self.tile_sprites.draw(self.screen)
      self.draw_slots()
      self.draw_wall_clock()
      self.draw_floating_text()
      self.draw_score()
      self.score_sprites.draw(self.screen)
      pygame.display.flip()

def main():
  game = Game()
  game.run()

if __name__ == '__main__':
  main()
