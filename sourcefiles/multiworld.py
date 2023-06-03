import io
import json
from typing import Optional

import ctenums
from ctenums import ItemID, CharID, LocID, RecruitID
import ctevent
import ctrom
import ctstrings
from eventcommand import EventCommand, Operation
import logicfactory
import logictypes
import randosettings as rset
import randoconfig as cfg
from freespace import FSWriteType


class CommandNotFoundException(Exception):
    pass


# These values are used when writing player info that will be used
# to validate the ROM in the multiworld client.
# 32 bytes reserved
#   - 16 character name limit
#   - 2 characters to glue an "AP" on the front
#   - 3 bytes for version information
#   - 11 bytes reserved in case we ever need it
MULTIWORLD_ID_ADDRESS = 0x5E0000
MULTIWORLD_ID_SIZE = 32
PLAYER_NAME_SIZE = 16
VERSION = bytes([0, 0, 1])


def _get_item_data(settings: rset.Settings, config: cfg.RandoConfig) -> list[dict[str, str]]:
    """
    Get item definitions for the multiworld config.

    This will pull key item data from the rando config and populate a list
    to be used in the AP yaml file.  It also includes "Event" entries for the characters
    to be used in the logic where required.

    :param settings: Randomizer settings object
    :param config: RandoConfig object to pull item data from.
    :return: List of item data entries
    """
    item_data = []

    # Items
    for location in config.key_item_locations:
        key_item = location.get_key_item()
        # Lost Worlds adds character specific items after the initial logical placement.
        # Filter these out if it is not a chronosanity seed so that we don't end up with
        # key items in locations outside the expected baseline logic locations.
        #
        # This will allow extra items to be added in cases like Legacy of Cyrus where there are
        # more locations than key items, though the item will be some piece of gear and will
        # show up on a normal key item location.
        valid_key = True
        if settings.game_mode == rset.GameMode.LOST_WORLDS and \
                rset.GameFlags.CHRONOSANITY not in settings.gameflags:
            if location.get_key_item() in [ItemID.ROBORIBBON, ItemID.MASAMUNE_2, ItemID.HERO_MEDAL]:
                valid_key = False

        if valid_key:
            if key_item == ItemID.MASAMUNE_2:
                # Grand Leon and HeroMedal are special cases.  The name in the DB can be different
                # depending on game mode or gear rando.  Always use "Grand Leon" for multiworld output.
                item_name = "Grand Leon"
            elif key_item == ItemID.HERO_MEDAL:
                item_name = "Hero Medal"
            else:
                item_name = config.itemdb[key_item].get_name_as_str(True)

            item_data.append({
                "name": item_name,
                "id": key_item,
                "classification": "progression"
            })

    return item_data


def _get_access_rules(logic_rule: logictypes.LogicRule, config: cfg.RandoConfig) -> list[list[str]]:
    """
    Convert the logic rule used for a location group into a multiworld format.

    :param logic_rule: The logic rule from a location group
    :param config: RandoConfig object used for item names
    :return: Rule converted for multiworld
    """
    mw_rule = []
    for rule in logic_rule.get_access_rule():
        mw_req_list = []
        for requirement in rule:
            if requirement in ctenums.ItemID:
                # Handle Grand Leon and Hero Medal in their own cases.  Their names can
                # change based on game mode or gear rando.
                if requirement == ItemID.MASAMUNE_2:
                    mw_req_list.append("Grand Leon")
                elif requirement == ItemID.HERO_MEDAL:
                    mw_req_list.append("Hero Medal")
                else:
                    mw_req_list.append(config.itemdb[requirement].get_name_as_str(True))
            else:
                # Character requirement
                mw_req_list.append(str(requirement))
        mw_rule.append(mw_req_list)

    return mw_rule


def _get_location_data(settings: rset.Settings, config: cfg.RandoConfig) -> list[dict[str, str]]:
    """
    Get location definitions for the multiworld config.

    :param settings: Randomizer settings object
    :param config: RandoConfig object to pull item data from
    :return: List of location data entries
    """
    location_data = []
    logic_config = logicfactory.get_game_config(settings, config)

    # Add key item locations
    for location in config.key_item_locations:
        location_group = logic_config.get_location_group_from_location(location)
        # NOTE:
        # It is possible for some character specific items to be put in chronosanity locations in a
        # non-chronosanity Lost Worlds game.  This can cause location_group to come back as
        # None since the location isn't part of the logic config.  Skip these spots
        # so that critical items can't end up in unexpected locations.
        valid_key = True
        if settings.game_mode == rset.GameMode.LOST_WORLDS and \
                rset.GameFlags.CHRONOSANITY not in settings.gameflags:
            if location.get_key_item() in [ItemID.ROBORIBBON, ItemID.MASAMUNE_2, ItemID.HERO_MEDAL]:
                valid_key = False

        if location_group is not None and valid_key:
            if location.get_treasure_id() == ctenums.TreasureID.PYRAMID_LEFT:
                # In a non-multiworld game, both pyramid chests hold the same item and the player
                # can only get one.  The pyramid location will return the ID of the left chest when
                # queried for a treasure ID.  Use this to specify only the left chest in the yaml
                # so that the right chest can be filled with some other junk fill item.
                # Both will be honored by the client when one is collected.
                loc_name = str(location.get_treasure_id())
            else:
                loc_name = location.get_name()

            location_data.append({
                "name": loc_name,
                "classification": "default",
            })

    # Add character locations
    for recruit_spot in config.char_assign_dict.keys():
        logic_rule = logic_config.get_game().get_char_rule(recruit_spot)
        if logic_rule is not None:
            location_data.append({
                "name": str(recruit_spot),
                "classification": "event",
                "character": str(f"{config.char_assign_dict[recruit_spot].held_char}")
            })

    return location_data


def _get_victory_conditions(settings: rset.Settings, config: cfg.RandoConfig) -> list[list[str]]:
    """
    Determine the victory conditions and rules for this seed.

    These will be used on the Archipelago side to create victory events for the spoiler log.

    :param settings: RandoSettings object with game settings
    :param config: RandoConfig object to pull item data from.
    :return: List of rules for victory
    """
    # TODO: Bundle this into logic configs?  Gets a lot more complicated with objectives.
    rules = []
    if settings.game_mode in [rset.GameMode.STANDARD, rset.GameMode.VANILLA_RANDO]:
        rules.append([ItemID.GATE_KEY, ItemID.DREAMSTONE, ItemID.RUBY_KNIFE])
        rules.append([ItemID.PENDANT, ItemID.CLONE, ItemID.C_TRIGGER])
        rules.append([ItemID.BENT_SWORD, ItemID.BENT_HILT, CharID.FROG])
    elif settings.game_mode == rset.GameMode.LOST_WORLDS:
        rules.append([ItemID.DREAMSTONE, ItemID.RUBY_KNIFE])
        rules.append([ItemID.CLONE, ItemID.C_TRIGGER])
    elif settings.game_mode == rset.GameMode.LEGACY_OF_CYRUS:
        rules.append([ItemID.BENT_HILT, ItemID.BENT_SWORD, ItemID.MASAMUNE_2,
                      CharID.FROG, CharID.MAGUS])
    elif settings.game_mode == rset.GameMode.ICE_AGE:
        rule = [ItemID.GATE_KEY, ItemID.DREAMSTONE, CharID.AYLA]
        dactyl_recruit = config.char_assign_dict[RecruitID.DACTYL_NEST]
        if dactyl_recruit.held_char is not CharID.AYLA:
            rule.append(dactyl_recruit.held_char)
        rules.append(rule)

    # TODO: Bucket fragments.  Just ignore bucket fragments as a go mode for now.

    # convert lists of keys/characters into strings.
    stringified_rules = []
    for rule in rules:
        temp = []
        for requirement in rule:
            if requirement in ItemID:
                if requirement == ItemID.MASAMUNE_2:
                    temp.append("Grand Leon")
                elif requirement == ItemID.HERO_MEDAL:
                    temp.append("Hero Medal")
                else:
                    temp.append(config.itemdb[requirement].get_name_as_str(True))
            else:
                temp.append(str(requirement))
        stringified_rules.append(temp)

    return stringified_rules


def _get_location_access_rules(settings: rset.Settings, config: cfg.RandoConfig) -> dict[str, list[list[str]]]:
    """
    Get a dictionary of access rules using the location name as a key.

    :param settings: RandoSettings object with game settings
    :param config: RandoConfig object to pull config data from
    :return: Dictionary of access rules by location
    """
    logic_config = logicfactory.get_game_config(settings, config)

    rules = {}
    # Key item locations
    for location in config.key_item_locations:
        location_group = logic_config.get_location_group_from_location(location)
        # Filter out spots used for non-key items, i.e. Hero Medal in a Lost Worlds seed
        if location_group is not None:
            rules[location.get_name()] = _get_access_rules(location_group.get_access_rule(), config)

    # Character recruitment locations
    for recruit_spot in config.char_assign_dict.keys():
        logic_rule = logic_config.get_game().get_char_rule(recruit_spot)
        if logic_rule is not None:
            # Skip unavailable locations (like Cathedral in Lost Worlds)
            rules[str(recruit_spot)] = _get_access_rules(logic_rule, config)

    return rules


def _apply_zombor_flag_fix(ct_rom: ctrom.CTRom):
    """
    Move the flag that tracks the Zombor battle from before the battle
    begins to after the battle ends.

    This will ensure that players have to actually finish the Zombor check to
    obtain or send the key item in multiworld.

    :param ct_rom: ROM data to modify
    """

    # Get the duplicate of Zenan Bridge since this is always where the boss
    # is fought now
    script = ct_rom.script_manager.get_script(
        ctenums.LocID.ZENAN_BRIDGE_BOSS
    )

    zombor_flag = EventCommand.assign_val_to_mem(0x02, 0x7F0101, 1)
    pos: Optional[int] = script.find_exact_command(zombor_flag)

    if pos is None:
        raise CommandNotFoundException

    script.delete_commands(pos, 1)

    # Zombor fight should be the next battle command after the flag set.
    pos, cmd = script.find_command([0xD8], pos)

    if pos is None:
        raise CommandNotFoundException

    pos += len(cmd)
    script.insert_commands(zombor_flag.to_bytearray(), pos)


def _apply_melchior_flag_fix(ct_rom: ctrom.CTRom):
    """
    Add a flag for the Melchior check.

    The Melchior check was previously tracked by reading 0x7F006D & 0x10,
    which is a bit that gets reused for several Melchior appearances.
    There is no dedicated memory flag for the sunstone turn in.  This function
    will add a flag for this check that can be more accurately tracked.

    :param ct_rom: ROM object to modify
    """
    script = ct_rom.script_manager.get_script(
        ctenums.LocID.GUARDIA_REAR_STORAGE
    )

    # The Melchior bit is set after the King's Trial, allowing Melchior to appear
    # in the guardia storage room.  It resets after the sunstone turn in.
    #
    # Find the command that resets the Melchior bit
    melchior_bit_cmd = EventCommand.reset_bit(0x7F006D, 0x10)
    pos: Optional[int] = script.find_exact_command(melchior_bit_cmd)

    # Make sure we actually found the command
    if pos is None:
        raise CommandNotFoundException

    # Insert a command to set the new flag bit.
    new_flag_cmd = EventCommand.set_bit(0x7F001F, 0x80)
    script.insert_commands(new_flag_cmd.to_bytearray(), pos)


def _add_victory_flag(ct_rom: ctrom.CTRom):
    """
    Add a flag to the ending selector screen so that we can easily track a victory condition.

    :param ct_rom: ROM object to update
    """
    script = ct_rom.script_manager.get_script(
        ctenums.LocID.ENDING_SELECTOR
    )

    # Add a flag at the beginning of the ending selector startup
    explore_mode_off_cmd = EventCommand.set_explore_mode(False)
    pos: Optional[int] = script.find_exact_command(explore_mode_off_cmd)

    if pos is None:
        raise CommandNotFoundException

    pos = pos + len(explore_mode_off_cmd)
    victory_flag_cmd = EventCommand.set_bit(0x7F0020, 0x01)
    script.insert_commands(victory_flag_cmd.to_bytearray(), pos)


def _apply_item_delivery_script_changes(ct_rom: ctrom.CTRom):
    """
    Apply the item delivery script to every location where we want the
    player to be able to receive items.  Also zero out the received
    items counter memory since it is initially filled with junk data.

    :param ct_rom: ROM data to modify
    """

    # These are the locations we don't want to be capable of delivering items.
    # TODO: Guardia Forest 600 crashes (presumably due to too many objects).  We can either leave it
    #       in the exclusion list or remove some of the unused objects (Frog flashback stuff).
    #       If we remove objects, we'll need to make sure the tab and sealed chest object IDs are
    #       updated elsewhere in the randomizer.
    location_exclusion_list = [LocID.LOAD_SCREEN, LocID.ENDING_SELECTOR, LocID.GUARDIA_FOREST_600]

    ef = ctevent.EF
    ec = ctevent.EC

    # Zero out the received items counter on the load screen (It's initially populated with junk data)
    # There are several other memory locations being cleared out here, so add ours to the list
    script = ct_rom.script_manager.get_script(ctenums.LocID.LOAD_SCREEN)

    cmd = ec.assign_val_to_mem(0, 0x7F0057, 1)
    pos = script.find_exact_command(cmd)

    # Make sure we actually found the command
    if pos is None:
        raise CommandNotFoundException

    pos += len(cmd)
    script.insert_commands(ec.assign_val_to_mem(0, 0x7E287C, 1).to_bytearray(), pos)

    # loop through all locations to add the item receive loop
    # Skip location IDs in the exclusion list.
    for location in LocID:
        if location in location_exclusion_list:
            continue

        script = ct_rom.script_manager.get_script(location)

        item_rec_str = "Received {item}!{null}"
        item_rec_ct_str = ctstrings.CTString.from_str(item_rec_str)
        item_rec_ct_str.compress()
        item_rec_str_id = script.add_string(item_rec_ct_str)

        # TODO: Add a check for explore mode.  We don't want to toggle explore mode back on if it
        #       is off for a cut scene or other reason when this event fires.
        # TODO: Increment received item counter (0x7E287C)?  Not in script memory.  How to do this?
        receive_function = ef()
        (
            receive_function
            .add(ec.return_cmd())
            .add(ec.generic_one_arg(0x87, 0x20))  # Set script speed slower to reduce potential lag
            .set_label("item_receive_loop")
            .add(ec.assign_mem_to_mem(0x7E298A, 0x7F03E0, 1))
            .add_if(
                # Check if saving is enabled.  If it is, don't run the loop.
                # Players can get stuck on save points with the item delivery text preventing movement
                # and the save point eating the A input to dismiss the text box.
                ec.if_mem_op_value(0x7F01CF, Operation.BITWISE_AND_NONZERO, 0x80, 1, 00),
                ef().jump_to_label(ec.jump_back(0), "item_receive_loop")
            )
            .add_if(
                ec.if_mem_op_value(0x7F03E0, Operation.NOT_EQUALS, 0, 1, 0),
                ef()
                .add(ec.generic_one_arg(0x87, 0x04))  # Speed up processing while receiving an item
                .add(ec.set_explore_mode(False))
                .add(ec.assign_mem_to_mem(0x7F03E0, 0x7F0200, 1))
                .add(ec.generic_one_arg(0xC7, 0x7F0200))  # Add Item to inventory from memory
                .add(ec.text_box(item_rec_str_id, False))
                .add(ec.assign_val_to_mem(0, 0x7E298A, 1))  # Reset the item delivery memory
                .add(ec.assign_val_to_mem(0, 0x7F03E0, 1))
                .add(ec.set_explore_mode(True))
                .add(ec.generic_one_arg(0x87, 0x20))  # Back to slow mode
            )
            .jump_to_label(ec.jump_back(0), "item_receive_loop")
        )

        new_obj_id = script.append_empty_object()
        script.set_function(new_obj_id, 0, receive_function)


def generate_yaml_ap_config(settings: rset.Settings, config: cfg.RandoConfig) -> io.StringIO:
    """
    Generate the config file used by Archipelago to generate the multiworld.

    We're actually creating a json file here.  Since yaml is a superset of
    json then Archipelago should be able to read it just fine.

    :param settings: RandoSettings object with game settings
    :param config: RandoConfig object to pull config data from
    :return: StringIO object with archipelago config as yaml
    """
    ap_cfg_dict = {
        "game": "Chrono Trigger Jets of Time",
        "name": settings.player_name,
        "Chrono Trigger Jets of Time": {
            "game_mode": str(settings.game_mode),
            "item_difficulty": str(settings.item_difficulty),
            "tab_treasures": rset.GameFlags.TAB_TREASURES in settings.gameflags,
            "bucket_fragments": rset.GameFlags.BUCKET_FRAGMENTS in settings.gameflags,
            "fragment_count": settings.bucket_settings.num_fragments,
            "items": _get_item_data(settings, config),
            "locations": _get_location_data(settings, config),
            "rules": _get_location_access_rules(settings, config),
            "victory": _get_victory_conditions(settings, config)
        }
    }

    ap_cfg_json = io.StringIO()
    json.dump(ap_cfg_dict, ap_cfg_json, indent=2)
    return ap_cfg_json


def apply_multiworld_changes(ct_rom: ctrom.CTRom, settings: rset.Settings, config: cfg.RandoConfig):
    """
    Apply the multiworld ROM changes to allow items to be given to the player as
    well as several minor fixes to improve multiworld tracking.

    :param ct_rom: ROM data to modify
    :param settings: Randomizer settings object
    :param config: Randomizer configuration object
    """
    _apply_zombor_flag_fix(ct_rom)
    _apply_melchior_flag_fix(ct_rom)
    _apply_item_delivery_script_changes(ct_rom)
    _add_victory_flag(ct_rom)

    # Place APItems in every chronosanity location for this game mode
    # even if the chosen game mode is not chronosanity.  The Archipelago
    # implementation will only allow key items to be placed in the locations
    # that were chosen for key items by the randomizer, but will place
    # useful and junk fill items in all other chronosanity locations.
    flags_backup = settings.gameflags
    settings.gameflags |= rset.GameFlags.CHRONOSANITY
    logic_config = logicfactory.get_game_config(settings, config)

    for location_group in logic_config.get_locations():
        for location in location_group.get_locations():
            config.treasure_assign_dict[location.get_treasure_id()].held_item = ctenums.ItemID.APITEM

    # Restore original flags
    settings.gameflags = flags_backup


def create_archipelago_item(settings: rset.Settings, config: cfg.RandoConfig):
    """
    Apply multiworld changes to the game config.

    NOTE: This must be called after item placement has occurred.

    :param settings: Settings object so that we can check game flags
    :param config: Config object to update for multiworld
    """
    if rset.GameFlags.MULTIWORLD not in settings.gameflags:
        return

    # Create an item to be used as a multiworld placeholder
    config.itemdb[ctenums.ItemID.APITEM].name = \
        ctstrings.CTNameString.from_string(' APItem', 0xB)


def reserve_free_space(ct_rom: ctrom.CTRom, settings: rset.Settings):
    """
    Reserve free space in the ROM to write data used to identify the user
    in a multiworld game.

    :param ct_rom: ROM object to reserve free space
    :param settings: Settings object
    :raises ValueError: When the multiworld player data address is not free space on the ROM
    """
    # block = (MULTIWORLD_ID_ADDRESS, MULTIWORLD_ID_SIZE)
    # space_manager = ct_rom.script_manager.fsrom.space_manager

    # Make sure that something else didn't sneak in and take our address!
    # TODO: Apparently this function doesn't work?
    # if not space_manager.is_block_free(block):
    #    raise ValueError("Multiworld player data is not free space!")

    data = bytearray()
    data.extend("AP".encode('ascii'))
    data.extend(VERSION)
    name = settings.player_name
    if len(name) > PLAYER_NAME_SIZE:
        name = name[0:PLAYER_NAME_SIZE]
    data.extend(name.encode('ascii'))

    # write the ID information to the ROM
    ct_rom.rom_data.seek(MULTIWORLD_ID_ADDRESS)
    ct_rom.rom_data.write(data, FSWriteType.MARK_USED)
