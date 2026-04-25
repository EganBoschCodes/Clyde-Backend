from home_assistant_lib import MediaPlayer

import clyde.utils as utils


def resolve_media_player(name: str) -> utils.Result[MediaPlayer]:
    player = utils.CONFIG.media_players.get(name)
    if player is None:
        return utils.err(ValueError(f"Unknown media player '{name}'"))
    return utils.ok(player)
