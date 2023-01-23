import typing

from discord.app_commands import locale_str as _T


class _DescC(typing.TypedDict):
    name: _T


class _Desc(_DescC):
    description: _T


# Generic values
_map_code = _T("Overwatch Workshop Code")
_user = _T("User name")
_creator = _T("Creator name")
_map_name = _T("Overwatch map")
_map_type = _T("Type of parkour map")
_add = _T("add")
_remove = _T("remove")
_nickname = _T("User display name (within bot commands only)")
_record = _T("Record in HH:MM:SS.ss format")

# Generic args
_map_code_a = "map_code"
_creator_a = "creator"
_new_level_name_a = "new_level_name"
_level_name_a = "level_name"
_map_name_a = "map_name"
_user_a = "user"
_name_a = "name"
_nickname_a = "nickname"

# MAPS COG -----------------------------------------------------------------
map_maker_ = _Desc(name=_T("map-maker"), description=_T("Map maker only commands"))
map_maker_level = _Desc(name=_T("level"), description=_T("Edit levels"))
map_maker_creator = _Desc(name=_T(_creator_a), description=_T("Edit creators"))

creator_args = {_map_code_a: _map_code, _creator_a: _creator}
remove_creator = _Desc(name=_remove, description=_T("Remove a creator from your map"))
add_creator = _Desc(name=_add, description=_T("Add a creator to your map"))

_level_name = _T("Level name")
_new_level_name = _T("New level name")

add_level = _Desc(name=_add, description=_T("Add a level name to your map"))
add_level_args = {_map_code_a: _map_code, _new_level_name_a: _new_level_name}
remove_level = _Desc(name=_remove, description=_T("Remove a level name from your map"))
remove_level_args = {_map_code_a: _map_code, _level_name_a: _level_name}
edit_level = _Desc(name=_T("rename"), description=_T("Rename a level in your map"))
edit_level_args = {
    _map_code_a: _map_code,
    _new_level_name_a: _new_level_name,
    _level_name_a: _level_name,
}

submit_map = _Desc(
    name=_T("submit-map"), description=_T("Submit your map to the database")
)
submit_map_args = {_map_code_a: _map_code, _map_name_a: _map_name}

map_search = _Desc(
    name=_T("map-search"), description=_T("Search for maps based on various filters")
)
map_search_args = {
    "map_type": _map_type,
    _map_name_a: _map_name,
    _creator_a: _creator,
    _map_code_a: _map_code,
}

view_guide = _Desc(name=_T("guide"), description=_T("View guide(s) for a specific map"))
view_guide_args = {_map_code_a: _map_code}
add_guide = _Desc(
    name=_T("add-guide"), description=_T("Add a guide for a specific map")
)
add_guide_args = {
    _map_code_a: _map_code,
    "url": _T("Valid URL to guide (YouTube, Streamable, etc)"),
}

# MOD COG -----------------------------------------------------------------
mod_ = _Desc(name=_T("mod"), description=_T("Mod only commands"))
keep_alive_ = _Desc(name=_T("keep-alive"), description=_T("Keep threads alive"))
add_keep_alive = _Desc(name=_add, description=_T("Add a keep-alive to a thread"))
remove_keep_alive = _Desc(
    name=_remove, description=_T("Remove a keep-alive from a thread")
)
keep_alive_args = {"thread": _T("Thread")}

remove_record = _Desc(
    name=_T("remove-record"), description=_T("Remove a record from a user")
)
remove_record_args = {
    _user_a: _user,
    _map_code_a: _map_code,
    _level_name_a: _level_name,
}

change_name = _Desc(
    name=_T("change-name"), description=_T("Change a user's display name")
)
change_name_args = {_user_a: _user, _nickname_a: _nickname}

# PERSONAL COG -----------------------------------------------------------------
alerts = _Desc(
    name=_T("alerts"), description=_T("Toggle Doombot verification alerts on/off")
)
alerts_args = {"value": _T("Alerts on/off")}

name = _Desc(
    name=_T(_name_a), description=_T("Change your display name in bot commands")
)
name_args = {_nickname_a: _nickname}

brug_mode = _Desc(name=_T("brug-mode"), description=_T("Emojify text"))
uwufier = _Desc(name=_T("uwu"), description=_T("UwUfy text"))
fun_args = {"text": _T("Text")}

blarg = _Desc(name=_T("blarg"), description=_T("BLARG"))

u = _Desc(name=_T("u"), description=_T("Insult someone"))
u_args = {_user_a: _user}

increase = _Desc(name=_T("increase"), description=_T("Increase! Beware the knife..."))
decrease = _Desc(
    name=_T("decrease"), description=_T("Decrease! Beware the growth pills...")
)

# RECORDS COG --------------------------------------------------
personal_records_c = _DescC(name=_T("personal-records"))
world_records_c = _DescC(name=_T("world-records"))

submit_record = _Desc(
    name=_T("submit-record"),
    description=_T(
        "Submit a record to the database. Video proof is required for full verification!"
    ),
)
submit_record_args = {
    _map_code_a: _map_code,
    _level_name_a: _level_name,
    "record": _record,
    "screenshot": _T("Screenshot of completion"),
    "video": _T("Video of play through. REQUIRED FOR FULL VERIFICATION!"),
    "rating": _T("What would you rate the quality of this level?"),
}

leaderboard = _Desc(
    name=_T("leaderboard"),
    description=_T("View leaderboard of any map in the database."),
)
leaderboard_args = {
    _map_code_a: _map_code,
    _level_name_a: _level_name,
    "verified": _T("Only show fully verified video submissions"),
}

personal_records = _Desc(
    name=_T("personal-records"),
    description=_T("View your (by default) personal records or another users)"),
)
personal_records_args = {
    _user_a: _user,
    "wr_only": _T("Only show world records, if any"),
}

# TAGS COG ----------------------------------------------
tags = _DescC(name=_T("tag"))
view_tag = _Desc(name=_T("view"), description=_T("View a tag"))
view_tag_args = {_name_a: _T("Name of the tag")}
create_tag = _Desc(name=_T("create"), description=_T("Create a tag"))
