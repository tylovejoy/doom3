import typing


class _DescC(typing.TypedDict):
    name: str


class _Desc(_DescC):
    description: str


# Generic values
_map_code = "Overwatch share code"
_user = "User name"
_creator = "Creator name"
_map_name = "Overwatch map"
_map_type = "Type of parkour map"
_add = "add"
_remove = "remove"
_nickname = "User display name (within bot commands only)"
_record = "Record in HH:MM:SS.ss format"

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
map_maker_ = _Desc(name="map-maker", description="Map maker only commands")
map_maker_level = _Desc(name="level", description="Edit levels")
map_maker_creator = _Desc(name=_creator_a, description="Edit creators")

creator_args = {_map_code_a: _map_code, _creator_a: _creator}
remove_creator = _Desc(name=_remove, description="Remove a creator from your map")
add_creator = _Desc(name=_add, description="Add a creator to your map")

_level_name = "Level name"
_new_level_name = "New level name"

add_level = _Desc(name=_add, description="Add a level name to your map")
add_level_args = {_map_code_a: _map_code, _new_level_name_a: _new_level_name}
remove_level = _Desc(name=_remove, description="Remove a level name from your map")
remove_level_args = {_map_code_a: _map_code, _level_name_a: _level_name}
edit_level = _Desc(name="rename", description="Rename a level in your map")
edit_level_args = {_map_code_a: _map_code, _new_level_name_a: _new_level_name, _level_name_a: _level_name}

submit_map = _Desc(name="submit-map", description="Submit your map to the database")
submit_map_args = {_map_code_a: _map_code, _map_name_a: _map_name}

map_search = _Desc(name="map-search", description="Search for maps based on various filters")
map_search_args = {"map_type": _map_type, _map_name_a: _map_name, _creator_a: _creator, _map_code_a: _map_code}

view_guide = _Desc(name="guide", description="View guide(s) for a specific map")
view_guide_args = {_map_code_a: _map_code}
add_guide = _Desc(name="add-guide", description="Add a guide for a specific map")
add_guide_args = {_map_code_a: _map_code, "url": "Valid URL to guide (YouTube, Streamable, etc)"}

# MOD COG -----------------------------------------------------------------
mod_ = _Desc(name="mod", description="Mod only commands")
keep_alive_ = _Desc(name="keep-alive", description="Keep threads alive")
add_keep_alive = _Desc(name=_add, description="Add a keep-alive to a thread")
remove_keep_alive = _Desc(name=_remove, description="Remove a keep-alive from a thread")
keep_alive_args = {"thread": "Thread"}

remove_record = _Desc(name="remove-record", description="Remove a record from a user")
remove_record_args = {_user_a: _user, _map_code_a: _map_code, _level_name_a: _level_name}

change_name = _Desc(name="change-name", description="Change a user's display name")
change_name_args = {_user_a: _user, _nickname_a: _nickname}

# PERSONAL COG -----------------------------------------------------------------
alerts = _Desc(name="alerts", description="Toggle Doombot verification alerts on/off")
alerts_args = {"value": "Alerts on/off"}

name = _Desc(name=_name_a, description="Change your display name in bot commands")
name_args = {_nickname_a: _nickname}

brug_mode = _Desc(name="brug-mode", description="Emojify text")
uwufier = _Desc(name="uwu", description="UwUfy text")
fun_args = {"text": "Text"}

blarg = _Desc(name="blarg", description="BLARG")

u = _Desc(name="u", description="Insult someone")
u_args = {_user_a: _user}

increase = _Desc(name="increase", description="Increase! Beware the knife...")
decrease = _Desc(name="decrease", description="Decrease! Beware the growth pills...")

# RECORDS COG --------------------------------------------------
personal_records_c = _DescC(name="personal-records")
world_records_c = _DescC(name="world-records")

submit_record = _Desc(
    name="submit-record",
    description="Submit a record to the database. Video proof is required for full verification!",
)
submit_record_args = {
    _map_code_a: _map_code,
    _level_name_a: _level_name,
    "record": _record,
    "screenshot": "Screenshot of completion",
    "video": "Video of play through. REQUIRED FOR FULL VERIFICATION!",
    "rating": "What would you rate the quality of this level?",
}

leaderboard = _Desc(name="leaderboard", description="View leaderboard of any map in the database.")
leaderboard_args = {_map_code_a: _map_code, _level_name_a: _level_name, "verified": "Only show fully verified video submissions"}

personal_records = _Desc(name="personal-records", description="View your (by default) personal records or another users")
personal_records_args = {_user_a: _user, "wr_only": "Only show world records, if any"}

# TAGS COG ----------------------------------------------
tags = _DescC(name="tag")
view_tag = _Desc(name="view", description="View a tag")
view_tag_args = {_name_a: "Name of the tag"}
create_tag = _Desc(name="create", description="Create a tag")






