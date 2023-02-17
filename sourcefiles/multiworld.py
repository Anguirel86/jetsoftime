import ctenums
import ctstrings
import io
import json
import logictypes
import randosettings as rset
import randoconfig as cfg


def get_item_data(config: cfg.RandoConfig) -> list[dict[str, str]]:
    """
    Get item definitions for the multiworld config.

    This will pull key item data from the rando config and populate a list
    to be used in the AP yaml file.  It also includes "Event" entries for the characters
    to be used in the logic where required.

    :param config: RandoConfig object to pull item data from.
    :return: List of item data entries
    """
    item_data = []

    # Items
    for location in config.key_item_locations:
        key_item = location.get_key_item()
        item_name = config.itemdb[key_item].get_name_as_str(True)
        # TODO - Currently all KIs are classified as progression
        #        May need to reclassify non-progression items like Jerky
        item_data.append({
            "name": item_name,
            "id": key_item,
            "classification": "progression"
        })

    # Add characters to the item array as events ("None" classification)
    for recruit_spot in config.char_assign_dict.keys():
        # TODO - Figure out character IDs.
        #        For now just make them (0x100 + charID) to not conflict with items.
        item_data.append({
            "name": str(f"{config.char_assign_dict[recruit_spot].held_char}"),
            "id": config.char_assign_dict[recruit_spot].held_char + 0x100,
            "classification": "None"
        })

    return item_data


def get_access_rules(location: logictypes.Location):
    """
    Determine the access rules for a given location.
    TODO: This is really hacky and should be a part of the actual placement logic
          so that we don't have to maintain two different logic engines.
    """
    pass


def get_location_data(settings: rset.Settings, config: cfg.RandoConfig) -> list[dict[str, str]]:
    """
    Get location definitions for the multiworld config.

    :param settings: Randomizer settings object
    :param config: RandoConfig object to pull item data from.
    :return: List of location data entries
    """
    location_data = []

    # Add key item locations
    for location in config.key_item_locations:
        # TODO - Location IDs need to be unique across worlds.  Need to figure this out.
        location_data.append({
            "name": location.get_name(),
            "id": 0,
            "classification": "default",
            "is_event:": False,
            "access_rules:": get_access_rules(location)
        })


    # Add character locations
    for recruit_spot in config.char_assign_dict.keys():
        # TODO - Location IDs
        location_data.append({
            "name": str(f"{config.char_assign_dict[recruit_spot].held_char}"),
            "id": 0,
            "classification": "event",
            "is_event:": True
        })

    return location_data


def generate_yaml_ap_config(settings: rset.Settings, config: cfg.RandoConfig) -> io.StringIO:
    """
    Generate the config file used by Archipelago to generate the multiworld.

    We're actually creating a json file here.  Since yaml is a superset of
    json then Archipelago should be able to read it just fine.

    :param settings: RandoSettings object with game settings
    :param config: RandoConfig object to pull config data from
    """
    ap_cfg_dict = {
        "game": "Chrono Trigger Jets of Time",
        "name": settings.player_name,
        "items": get_item_data(config),
        "locations": get_location_data(config)
    }

    ap_cfg_json = io.StringIO()
    json.dump(ap_cfg_dict, ap_cfg_json, indent=2)
    return ap_cfg_json


def apply_multiworld_rom_changes(config: cfg.RandoConfig):
    """
    Apply the multiworld ROM changes to allow items to be given to the player.

    :param config: RandoConfig object
    """

    # Replace all placed key items with APItems.
    for location in config.key_item_locations:
        location.set_key_item(ctenums.ItemID.APITEM)


def generate_multiworld_config(settings: rset.Settings, config: cfg.RandoConfig):
    """
    Top level function to convert this game into a multiworld ready seed.
    """
    #if rset.GameFlags.MULTIWORLD not in settings.gameflags:
    #    return

    # Create an item to be used as a multiworld placeholder
    config.itemdb[ctenums.ItemID.APITEM].name = \
        ctstrings.CTNameString.from_string(' APItem', 0xB)

    # Make a yaml file with game config data for Archipelago to consume.
    temp = generate_yaml_ap_config(settings, config)
    print(temp.getvalue())

    # Apply multiworld specific ROM changes
    #apply_multiworld_rom_changes(config)

    # TODO: temp stuff to generate an item list
    #item_dict = {}
    #for item in ctenums.ItemID:
    #    item_dict[config.itemdb[item].get_name_as_str(True)] = item.value
