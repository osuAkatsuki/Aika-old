from typing import Any, Optional
from mysql.connector.pooling import MySQLConnectionPool
from time import time
from re import compile as re_compile, IGNORECASE
from os import path

start_time: float = time()

version = 5.01      # Aika (This bot).
abns_version = 3.06 # Akatsuki's Beatmap Nomination System (#rank-request(s)).

db: Optional[MySQLConnectionPool] = None
config: Optional[Any] = None
debug: bool = False

regex = {
    'beatmap': re_compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|o(ld|su)\.ppy\.sh|ripple\.moe)/b/(?P<beatmap_id>\d+)(/|\?mode=\d)?$', IGNORECASE),
    'beatmapset': re_compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|o(ld|su)\.ppy\.sh|ripple\.moe)/(s|d)/(?P<beatmapset_id>\d+)(/|\?mode=\d)?$', IGNORECASE),
    'discussion': re_compile(r'^((http)?s?://)?(www\.)?((gatari|akatsuki)\.pw|o(ld|su)\.ppy\.sh|ripple\.moe)/beatmapset/(?P<beatmapset_id>\d+)/discussion/(?P<beatmap_id>\d+)/?$', IGNORECASE)
}
