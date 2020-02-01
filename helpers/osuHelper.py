from typing import List, Tuple
from constants import mods

def mods_to_readable(m: int) -> str:
    if not m: return 'Nomod'

    s: List[str] = []
    if m & mods.NOFAIL:      s.append('NF')
    if m & mods.EASY:        s.append('EZ')
    if m & mods.TOUCHSCREEN: s.append('TD')
    if m & mods.HIDDEN:      s.append('HD')
    if m & mods.HARDROCK:    s.append('HR')
    if m & mods.SUDDENDEATH: s.append('SD')
    if m & mods.DOUBLETIME:  s.append('DT')
    if m & mods.RELAX:       s.append('RX')
    if m & mods.HALFTIME:    s.append('HT')
    if m & mods.NIGHTCORE:   s.append('NC')
    if m & mods.FLASHLIGHT:  s.append('FL')
    if m & mods.AUTOPLAY:    s.append('AU')
    if m & mods.SPUNOUT:     s.append('SO')
    if m & mods.RELAX2:      s.append('AP')
    if m & mods.PERFECT:     s.append('PF')
    if m & mods.KEY4:        s.append('4K')
    if m & mods.KEY5:        s.append('5K')
    if m & mods.KEY6:        s.append('6K')
    if m & mods.KEY7:        s.append('7K')
    if m & mods.KEY8:        s.append('8K')
    if m & mods.KEYMOD:      s.append('??')
    if m & mods.FADEIN:      s.append('FI')
    if m & mods.RANDOM:      s.append('RN')
    if m & mods.LASTMOD:     s.append('??')
    if m & mods.KEY9:        s.append('9K')
    if m & mods.KEY10:       s.append('10K')
    if m & mods.KEY1:        s.append('1K')
    if m & mods.KEY3:        s.append('3K')
    if m & mods.KEY2:        s.append('2K')
    if m & mods.SCOREV2:     s.append('SV2')
    return ', '.join(s)

def ranked_status_to_readable(i: int) -> str:
    return 'Ranked' if i == 2 else ('Loved' if i == 5 else 'Unranked')

def hitlength_to_readable(l: int) -> str:
    return f'{l // 60}:{str(l % 60).zfill(2)}'

def playtime_to_readable(t: int) -> str:
    d = int(t / 60 / 60 // 24)
    s = int(t % (60 * 60 * 24))
    return f'{d}d {int(s / 60 // 60)}h {t % (60 * 60) // 60}m'

def mode_to_readable(m: int) -> Tuple[str]:
    if m == 0: return ('std',   'osu!')
    if m == 1: return ('taiko', 'osu!taiko')
    if m == 2: return ('ctb',   'osu!catch')
    else:      return ('mania', 'osu!mania')
