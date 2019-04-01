# Author: echel0n <echel0n@sickrage.ca>
# URL: https://sickrage.ca
# Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#
# This file is part of SiCKRAGE.
#
# SiCKRAGE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SiCKRAGE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.


import datetime
import time
import traceback

from sqlalchemy import orm

import sickrage
from sickrage.core.databases.main import MainDB
from sickrage.core.helpers import findCertainShow, try_int
from sickrage.core.websession import WebSession
from sickrage.indexers import IndexerApi


def get_scene_numbering(indexer_id, indexer, season, episode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param indexer_id: int
    :param season: int
    :param episode: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    showObj = findCertainShow(int(indexer_id))
    if showObj and not showObj.is_scene:
        return season, episode

    result = find_scene_numbering(int(indexer_id), int(indexer), season, episode)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_numbering(int(indexer_id), int(indexer), season, episode)
            if xem_result:
                return xem_result
        return season, episode


def find_scene_numbering(indexer_id, indexer, season, episode):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    try:
        dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                             season=season, episode=episode).filter(
            MainDB.SceneNumbering.scene_season != 0 and MainDB.SceneNumbering.scene_episode != 0).one()
        return try_int(dbData.scene_season), try_int(dbData.scene_episode)
    except orm.exc.NoResultFound:
        return


def get_scene_absolute_numbering(indexer_id, indexer, absolute_number, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode), with the scene numbering (if there is one),
    otherwise returns the xem numbering (if fallback_to_xem is set), otherwise
    returns the TVDB numbering.
    (so the return values will always be set)

    :param indexer_id: int
    ;param absolute_number: int
    :param fallback_to_xem: bool If set (the default), check xem for matches if there is no local scene numbering
    :return: (int, int) a tuple with (season, episode)
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    showObj = findCertainShow(indexer_id)
    if showObj and not showObj.is_scene:
        return absolute_number

    result = find_scene_absolute_numbering(indexer_id, indexer, absolute_number)
    if result:
        return result
    else:
        if fallback_to_xem:
            xem_result = find_xem_absolute_numbering(indexer_id, indexer, absolute_number)
            if xem_result:
                return xem_result
        return absolute_number


def find_scene_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Same as get_scene_numbering(), but returns None if scene numbering is not set
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    try:
        dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                             absolute_number=absolute_number).filter(
            MainDB.SceneNumbering.scene_absolute_number != 0).one()
        return try_int(dbData.scene_absolute_number)
    except orm.exc.NoResultFound:
        return


def get_indexer_numbering(indexer_id, indexer, sceneSeason, sceneEpisode, fallback_to_xem=True):
    """
    Returns a tuple, (season, episode) with the TVDB numbering for (sceneSeason, sceneEpisode)
    (this works like the reverse of get_scene_numbering)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    try:
        dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                             scene_season=sceneSeason,
                                             scene_episode=sceneEpisode).one()
        return try_int(dbData.season), try_int(dbData.episode)
    except orm.exc.NoResultFound:
        if fallback_to_xem:
            return get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode)
        return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering(indexer_id, indexer, sceneAbsoluteNumber, fallback_to_xem=True, scene_season=None):
    """
    Returns a tuple, (season, episode, absolute_number) with the TVDB absolute numbering for (sceneAbsoluteNumber)
    (this works like the reverse of get_absolute_numbering)
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    try:
        if scene_season is None:
            dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                                 scene_absolute_number=sceneAbsoluteNumber).one()
        else:
            dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                                 scene_absolute_number=sceneAbsoluteNumber,
                                                 scene_season=scene_season).one()
        return try_int(dbData.absolute_number)
    except orm.exc.NoResultFound:
        if fallback_to_xem:
            return get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season)
        return sceneAbsoluteNumber


def set_scene_numbering(indexer_id, indexer, season=0, episode=0, absolute_number=0, sceneSeason=0,
                        sceneEpisode=0, sceneAbsolute=0):
    """
    Set scene numbering for a season/episode.
    To clear the scene numbering, leave both sceneSeason and sceneEpisode as None.
    """
    if indexer_id is None:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    if season and episode:
        try:
            dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                                 season=season, episode=episode).one()
            dbData.scene_season = sceneSeason
            dbData.scene_episode = sceneEpisode
            MainDB.SceneNumbering.update(**dbData.as_dict())
        except orm.exc.NoResultFound:
            MainDB.SceneNumbering.add(**{
                'indexer': indexer,
                'indexer_id': indexer_id,
                'season': season,
                'episode': episode,
                'scene_season': sceneSeason,
                'scene_episode': sceneEpisode,
                'absolute_number': absolute_number,
                'scene_absolute_number': sceneAbsolute
            })
    elif absolute_number:
        try:
            dbData = MainDB.SceneNumbering.query(indexer_id=indexer_id, indexer=indexer,
                                                 absolute_number=absolute_number).one()
            dbData.scene_absolute_number = sceneAbsolute
            MainDB.SceneNumbering.update(**dbData.as_dict())
        except orm.exc.NoResultFound:
            MainDB.SceneNumbering.add(**{
                'indexer': indexer,
                'indexer_id': indexer_id,
                'season': season,
                'episode': episode,
                'scene_season': sceneSeason,
                'scene_episode': sceneEpisode,
                'absolute_number': absolute_number,
                'scene_absolute_number': sceneAbsolute
            })

    # Reload data from DB so that cache and db are in sync
    show = findCertainShow(indexer_id)
    show.flush_episodes()


def find_xem_numbering(indexer_id, indexer, season, episode):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param season: int
    :param episode: int
    :return: (int, int) a tuple of scene_season, scene_episode, or None if there is no special mapping.
    """
    if indexer_id is None or season is None or episode is None:
        return season, episode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    try:
        dbData = MainDB.TVEpisode.query(showid=indexer_id, indexer=indexer,
                                        season=season,
                                        episode=episode).filter(
            MainDB.TVEpisode.scene_season != 0, MainDB.TVEpisode.scene_episode != 0).one()

        return try_int(dbData.scene_season), try_int(dbData.scene_episode)
    except orm.exc.NoResultFound:
        return


def find_xem_absolute_numbering(indexer_id, indexer, absolute_number):
    """
    Returns the scene numbering, as retrieved from xem.
    Refreshes/Loads as needed.

    :param indexer_id: int
    :param absolute_number: int
    :return: int
    """
    if indexer_id is None or absolute_number is None:
        return absolute_number

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    try:
        dbData = MainDB.TVEpisode.query(showid=indexer_id, indexer=indexer, absolute_number=absolute_number).filter(
            MainDB.TVEpisode.scene_absolute_number != 0).one()
        return try_int(dbData.scene_absolute_number)
    except orm.exc.NoResultFound:
        return


def get_indexer_numbering_for_xem(indexer_id, indexer, sceneSeason, sceneEpisode):
    """
    Reverse of find_xem_numbering: lookup a tvdb season and episode using scene numbering

    :param indexer_id: int
    :param sceneSeason: int
    :param sceneEpisode: int
    :return: (int, int) a tuple of (season, episode)
    """
    if indexer_id is None or sceneSeason is None or sceneEpisode is None:
        return sceneSeason, sceneEpisode

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    try:
        dbData = MainDB.TVEpisode.query(showid=indexer_id, indexer=indexer, scene_season=sceneSeason,
                                        scene_episode=sceneEpisode).one()
        return try_int(dbData.season), try_int(dbData.episode)
    except orm.exc.NoResultFound:
        return sceneSeason, sceneEpisode


def get_indexer_absolute_numbering_for_xem(indexer_id, indexer, sceneAbsoluteNumber, scene_season=None):
    """
    Reverse of find_xem_numbering: lookup a tvdb season and episode using scene numbering

    :param indexer_id: int
    :param sceneAbsoluteNumber: int
    :return: int
    """
    if indexer_id is None or sceneAbsoluteNumber is None:
        return sceneAbsoluteNumber

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    try:
        if scene_season is None:
            dbData = MainDB.TVEpisode.query(showid=indexer_id, indexer=indexer,
                                            scene_absolute_number=sceneAbsoluteNumber).one()
        else:
            dbData = MainDB.TVEpisode.query(showid=indexer_id, indexer=indexer,
                                            scene_absolute_number=sceneAbsoluteNumber, scene_season=scene_season).one()
        return try_int(dbData.absolute_number)
    except orm.exc.NoResultFound:
        return sceneAbsoluteNumber


def get_scene_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    result = {}
    for dbData in MainDB.SceneNumbering.query(indexer_id=indexer_id):
        season = try_int(dbData.season)
        episode = try_int(dbData.episode)
        scene_season = try_int(dbData.scene_season)
        scene_episode = try_int(dbData.scene_episode)
        if try_int(dbData.indexer) != indexer or (scene_season or scene_episode) == 0:
            continue

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_xem_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    result = {}
    for dbData in MainDB.TVEpisode.query(showid=indexer_id):
        season = try_int(dbData.season)
        episode = try_int(dbData.episode)
        scene_season = try_int(dbData.scene_season)
        scene_episode = try_int(dbData.scene_episode)
        if try_int(dbData.indexer) != indexer or (scene_season or scene_episode) == 0:
            continue

        result[(season, episode)] = (scene_season, scene_episode)

    return result


def get_scene_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    result = {}
    for dbData in MainDB.SceneNumbering.query(indexer_id=indexer_id):
        absolute_number = try_int(dbData.absolute_number)
        scene_absolute_number = try_int(dbData.scene_absolute_number)
        if try_int(dbData.indexer) != indexer or scene_absolute_number == 0:
            continue

        result[absolute_number] = scene_absolute_number

    return result


def get_xem_absolute_numbering_for_show(indexer_id, indexer):
    """
    Returns a dict of (season, episode) : (sceneSeason, sceneEpisode) mappings
    for an entire show.  Both the keys and values of the dict are tuples.
    Will be empty if there are no scene numbers set in xem
    """
    if indexer_id is None:
        return {}

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    xem_refresh(indexer_id, indexer)

    result = {}
    for dbData in MainDB.TVEpisode.query(showid=indexer_id):
        absolute_number = try_int(dbData.absolute_number)
        scene_absolute_number = try_int(dbData.scene_absolute_number)
        if try_int(dbData.indexer) != indexer or scene_absolute_number == 0: continue

        result[absolute_number] = scene_absolute_number

    return result


def xem_refresh(indexer_id, indexer, force=False):
    """
    Refresh data from xem for a tv show

    :param indexer_id: int
    """
    if not indexer_id or indexer_id < 1:
        return

    indexer_id = int(indexer_id)
    indexer = int(indexer)

    MAX_REFRESH_AGE_SECS = 86400  # 1 day

    try:
        dbData = MainDB.XEMRefresh.query(indexer_id=indexer_id).one()
        lastRefresh = try_int(dbData.last_refreshed)
        refresh = int(time.mktime(datetime.datetime.today().timetuple())) > lastRefresh + MAX_REFRESH_AGE_SECS
    except orm.exc.NoResultFound:
        refresh = True

    if refresh or force:
        sickrage.app.log.debug(
            'Looking up XEM scene mapping for show %s on %s' % (indexer_id, IndexerApi(indexer).name))

        # mark refreshed
        try:
            dbData = MainDB.XEMRefresh.query(indexer_id=indexer_id).one()
            dbData.last_refreshed = int(time.mktime(datetime.datetime.today().timetuple()))
            MainDB.XEMRefresh.update(**dbData.as_dict())
        except orm.exc.NoResultFound:
            MainDB.XEMRefresh.add(**{
                'indexer': indexer,
                'last_refreshed': int(time.mktime(datetime.datetime.today().timetuple())),
                'indexer_id': indexer_id
            })

        try:
            # XEM MAP URL
            url = "http://thexem.de/map/havemap?origin=%s" % IndexerApi(indexer).config['xem_origin']

            try:
                parsedJSON = WebSession().get(url).json()
                if indexer_id not in map(int, parsedJSON['data']):
                    raise Exception
            except Exception:
                for dbData in MainDB.TVEpisode.query(showid=indexer_id):
                    dbData.scene_season = dbData.scene_episode = dbData.scene_absolute_number = 0
                    MainDB.TVEpisode.update(**dbData.as_dict())
                return

            # XEM API URL
            url = "http://thexem.de/map/all?id={}&origin={}&destination=scene".format(
                indexer_id, IndexerApi(indexer).config['xem_origin'])

            try:
                parsedJSON = WebSession().get(url).json()
                if 'success' not in parsedJSON['result']:
                    raise Exception
            except Exception:
                sickrage.app.log.info(
                    'No XEM data for show "%s on %s"' % (indexer_id, IndexerApi(indexer).name,))
                return

            for entry in parsedJSON['data']:
                try:
                    dbData = MainDB.TVEpisode.query(showid=indexer_id, season=
                    entry[IndexerApi(indexer).config['xem_origin']]['season'], episode=entry[
                        IndexerApi(indexer).config['xem_origin']]['episode']).one()
                except orm.exc.NoResultFound:
                    continue

                if 'scene' in entry:
                    dbData.scene_season = entry['scene']['season']
                    dbData.scene_episode = entry['scene']['episode']
                    dbData.scene_absolute_number = entry['scene']['absolute']
                if 'scene_2' in entry:  # for doubles
                    dbData.scene_season = entry['scene_2']['season']
                    dbData.scene_episode = entry['scene_2']['episode']
                    dbData.scene_absolute_number = entry['scene_2']['absolute']

                dbData.commit()

        except Exception as e:
            sickrage.app.log.warning(
                "Exception while refreshing XEM data for show {} on {}: {}".format(indexer_id,
                                                                                   IndexerApi(indexer).name,
                                                                                   e))
            sickrage.app.log.debug(traceback.format_exc())


def get_absolute_number_from_season_and_episode(show, season, episode):
    """
    Find the absolute number for a show episode

    :param show: Show object
    :param season: Season number
    :param episode: Episode number
    :return: The absolute number
    """

    absolute_number = None

    if season and episode:
        try:
            dbData = MainDB.TVEpisode.query(showid=show.indexerid, season=season, episode=episode).one()
            absolute_number = try_int(dbData.absolute_number)
            sickrage.app.log.debug(
                "Found absolute number %s for show %s S%02dE%02d" % (absolute_number, show.name, season, episode))
        except orm.exc.NoResultFound:
            sickrage.app.log.debug(
                "No entries for absolute number for show %s S%02dE%02d" % (show.name, season, episode))

    return absolute_number
