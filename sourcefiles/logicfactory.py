import copy
from math import ceil
import typing

from logictypes import BaselineLocation, Location, LocationGroup, \
    LinkedLocation, LogicRule, Game
import treasuredata as td

from ctenums import TreasureID as TID, CharID as Characters, ItemID, \
    RecruitID
import randosettings as rset
import randoconfig as cfg


#
# The LogicFactory is used by the logic writer to get a GameConfig
# object for the flags that the user selected.  The returned GameConfig
# object holds a list of all LocationGroups, KeyItems, and a configured
# Game object.  These are used by the logic writer to handle key item
# placement.
#

class GameConfig:
    """
    The GameConfig class holds the locations and key items associated with a
    game type.
    """

    def __init__(self,
                 settings: rset.Settings,
                 config: cfg.RandoConfig):
        self.keyItemList = []
        self.location_groups: list[LocationGroup] = []
        self.settings = settings
        self.config = config
        self.game = None
        self.init_locations()
        self.init_key_items()
        self.init_game()

    def init_locations(self):
        """
        Subclasses will override this method to
        initialize LocationGroups for their specific mode.
        """
        raise NotImplementedError()

    def init_key_items(self):
        """
        Subclasses will override this method to
        initialize key items for their specific mode.
        """
        raise NotImplementedError()

    def init_game(self):
        """
        Subclasses will override this method to
        configure a game object for their specific mode.
        """
        raise NotImplementedError()

    def update_key_items(self, key_item_list: list[ItemID]) -> list[ItemID]:
        """
        Update the key item list based on the current state of the game.
        Example: Chronosanity removes key item bias after some items are placed.

        :return: A potentially modified list of key items (e.g. weights)
        """

        # Since most modes do not bias anything, I'm setting the default
        # to do nothing.  Subclasses will override.
        return key_item_list

    def get_locations(self):
        """
        Get the LocationGroups associated with this game mode.

        :return: A list of LocationGroup objects for this mode
        """
        return self.location_groups

    def get_location_group(self, name: str) -> typing.Union[LocationGroup, None]:
        """
        Get the LocationGroup with the given name.

        :return: The LocationGroup object with the given name
        """
        try:
            return next(x for x in self.location_groups
                        if x.name == name)
        except StopIteration:
            return None

    def get_key_item_list(self) -> list[ItemID]:
        """
        Get the list of key items associated with this game mode.

        :return: A list of KeyItem objects for this mode
        """
        return self.keyItemList

    def get_game(self) -> Game:
        """
        Get the Game object associated with this mode.

        :return: A configured Game object for this mode
        """
        return self.game

    def remove_location_groups(
            self,
            names: typing.Union[str, typing.Iterable[str]]):
        """
        Remove all LocationGroups with the given names.

        :param names: A name or iterable of names of LocationGroups to remove
        """

        if isinstance(names, str):
            names = [names]

        removed_inds = (self.location_groups.index(x)
                        for x in self.location_groups
                        if x.name in names)

        for ind in sorted(removed_inds, reverse=True):
            del (self.location_groups[ind])

    def get_location_group_from_location(self, location: Location) -> typing.Union[LocationGroup, None]:
        """
        Get the location group that contains the given location
        """
        for group in self.location_groups:
            if group.has_location(location):
                return group
        return None


# end GameLogic class


class ChronosanityGameConfig(GameConfig):
    """
    This class represents the game configuration for a
    standard Chronosanity game.
    """

    def __init__(self, settings: rset.Settings,
                 config: cfg.RandoConfig):
        self.charLocations = config.char_assign_dict
        self.earlyPendant = rset.GameFlags.FAST_PENDANT in settings.gameflags
        self.lockedChars = rset.GameFlags.LOCKED_CHARS in settings.gameflags
        GameConfig.__init__(self, settings, config)
        apply_epoch_fail(self)

    def init_locations(self):
        # Dark Ages
        # Mount Woe does not go away in the randomizer, so it
        # is being considered for key item drops.

        darkages_locations = \
            LocationGroup("Darkages", 30,
                          LogicRule()
                          .add_rule([ItemID.GATE_KEY])
                          .add_rule([ItemID.PENDANT]))
        (
            darkages_locations
            .add_location(Location(TID.MT_WOE_1ST_SCREEN))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_1))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_2))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_3))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_4))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_5))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_1))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_2))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_3))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_4))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_5))
            .add_location(Location(TID.MT_WOE_FINAL_1))
            .add_location(Location(TID.MT_WOE_FINAL_2))
            .add_location(Location(TID.MT_WOE_KEY))
        )

        # Fiona Shrine (Key Item only)
        fiona_shrine_locations = \
            LocationGroup("Fionashrine", 2,
                          LogicRule().add_rule([Characters.ROBO]))
        (
            fiona_shrine_locations
            .add_location(Location(TID.FIONA_KEY))
        )

        # Future
        future_open_locations = \
            LocationGroup("FutureOpen", 20,
                          LogicRule().add_rule([ItemID.PENDANT]))
        (
            future_open_locations
            # Chests
            .add_location(Location(TID.ARRIS_DOME_RATS))
            .add_location(Location(TID.ARRIS_DOME_FOOD_STORE))
            # KeyItems
            .add_location(Location(TID.ARRIS_DOME_KEY))
            .add_location(Location(TID.SUN_PALACE_KEY))
        )

        future_sewers_locations = \
            LocationGroup("FutureSewers", 9,
                          LogicRule().add_rule([ItemID.PENDANT]))
        (
            future_sewers_locations
            .add_location(Location(TID.SEWERS_1))
            .add_location(Location(TID.SEWERS_2))
            .add_location(Location(TID.SEWERS_3))
        )

        future_lab_locations = \
            LocationGroup("FutureLabs", 15,
                          LogicRule().add_rule([ItemID.PENDANT]))
        (
            future_lab_locations
            .add_location(Location(TID.LAB_16_1))
            .add_location(Location(TID.LAB_16_2))
            .add_location(Location(TID.LAB_16_3))
            .add_location(Location(TID.LAB_16_4))
            .add_location(Location(TID.LAB_32_1))
            # 1000AD, opened after trial - putting it here to dilute the
            # lab pool a bit.
            .add_location(Location(TID.PRISON_TOWER_1000))
            # Race log chest is not included.
            # .add_location(Location(TID.LAB_32_RACE_LOG))
        )

        geno_dome_locations = \
            LocationGroup("GenoDome", 33, LogicRule().add_rule([ItemID.PENDANT]))
        (
            geno_dome_locations
            .add_location(Location(TID.GENO_DOME_1F_1))
            .add_location(Location(TID.GENO_DOME_1F_2))
            .add_location(Location(TID.GENO_DOME_1F_3))
            .add_location(Location(TID.GENO_DOME_1F_4))
            .add_location(Location(TID.GENO_DOME_ROOM_1))
            .add_location(Location(TID.GENO_DOME_ROOM_2))
            .add_location(Location(TID.GENO_DOME_PROTO4_1))
            .add_location(Location(TID.GENO_DOME_PROTO4_2))
            .add_location(Location(TID.GENO_DOME_2F_1))
            .add_location(Location(TID.GENO_DOME_2F_2))
            .add_location(Location(TID.GENO_DOME_2F_3))
            .add_location(Location(TID.GENO_DOME_2F_4))
            .add_location(Location(TID.GENO_DOME_KEY))
        )

        factory_locations = \
            LocationGroup("Factory", 30, LogicRule().add_rule([ItemID.PENDANT]))
        (
            factory_locations
            .add_location(Location(TID.FACTORY_LEFT_AUX_CONSOLE))
            .add_location(Location(TID.FACTORY_LEFT_SECURITY_RIGHT))
            .add_location(Location(TID.FACTORY_LEFT_SECURITY_LEFT))
            .add_location(Location(TID.FACTORY_RUINS_GENERATOR))
            .add_location(Location(TID.FACTORY_RIGHT_DATA_CORE_1))
            .add_location(Location(TID.FACTORY_RIGHT_DATA_CORE_2))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_TOP))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_LEFT))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_BOTTOM))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_SECRET))
            .add_location(Location(TID.FACTORY_RIGHT_CRANE_LOWER))
            .add_location(Location(TID.FACTORY_RIGHT_CRANE_UPPER))
            .add_location(Location(TID.FACTORY_RIGHT_INFO_ARCHIVE))
            # .add_location(Location(TID.FACTORY_ROBOT_STORAGE))
            # Inaccessible chest
        )

        # GiantsClawLocations
        giants_claw_locations = \
            LocationGroup("Giantsclaw", 30,
                          LogicRule().add_rule([ItemID.TOMAS_POP]))
        (
            giants_claw_locations
            .add_location(Location(TID.GIANTS_CLAW_KINO_CELL))
            .add_location(Location(TID.GIANTS_CLAW_TRAPS))
            .add_location(Location(TID.GIANTS_CLAW_CAVES_1))
            .add_location(Location(TID.GIANTS_CLAW_CAVES_2))
            .add_location(Location(TID.GIANTS_CLAW_CAVES_3))
            .add_location(Location(TID.GIANTS_CLAW_CAVES_4))
            # .add_location(Location(TID.GIANTS_CLAW_ROCK))
            .add_location(Location(TID.GIANTS_CLAW_CAVES_5))
            .add_location(Location(TID.GIANTS_CLAW_KEY))
        )

        # Northern Ruins
        northern_ruins_locations = \
            LocationGroup("NorthernRuins", 8,
                          LogicRule().add_rule([ItemID.MASAMUNE_2]))
        (
            northern_ruins_locations
            .add_location(Location(TID.NORTHERN_RUINS_BASEMENT_600))
            .add_location(Location(TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600))
            .add_location(Location(TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000))
            .add_location(Location(TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600))
            .add_location(Location(TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000))
            .add_location(Location(TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600))
            .add_location(Location(TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000))
            .add_location(Location(TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600))
            .add_location(Location(TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000))
        )

        northern_ruins_frog_locked = \
            LocationGroup(
                "NorthernRuinsFrogLocked", 1,
                LogicRule().add_rule([ItemID.MASAMUNE_2, Characters.FROG]))
        (
            northern_ruins_frog_locked
            .add_location(Location(TID.NORTHERN_RUINS_BASEMENT_1000))
        )

        # Guardia Treasury
        guardia_treasury_locations = \
            LocationGroup("GuardiaTreasury", 36,
                          LogicRule().add_rule([ItemID.PRISMSHARD, Characters.MARLE]))
        (
            guardia_treasury_locations
            .add_location(Location(TID.GUARDIA_BASEMENT_1))
            .add_location(Location(TID.GUARDIA_BASEMENT_2))
            .add_location(Location(TID.GUARDIA_BASEMENT_3))
            .add_location(Location(TID.GUARDIA_TREASURY_1))
            .add_location(Location(TID.GUARDIA_TREASURY_2))
            .add_location(Location(TID.GUARDIA_TREASURY_3))
            .add_location(Location(TID.KINGS_TRIAL_KEY))
        )

        # Ozzie's Fort locations
        # Ozzie's fort is a high level location.
        # For the first four chests, don't consider these locations until the
        # player has either the pendant or gate key.
        # As of 3.1.1, the back two chests are lumped in with the front four.
        early_ozzies_fort_locations = LocationGroup(
            "Ozzie's Fort", 12,
            LogicRule().add_rule([ItemID.PENDANT]).add_rule([ItemID.GATE_KEY]))
        (
            early_ozzies_fort_locations
            .add_location(Location(TID.OZZIES_FORT_GUILLOTINES_1))
            .add_location(Location(TID.OZZIES_FORT_GUILLOTINES_2))
            .add_location(Location(TID.OZZIES_FORT_GUILLOTINES_3))
            .add_location(Location(TID.OZZIES_FORT_GUILLOTINES_4))
            .add_location(Location(TID.OZZIES_FORT_FINAL_1))
            .add_location(Location(TID.OZZIES_FORT_FINAL_2))
        )

        # Open locations always available with no access requirements
        # Open locations are split into multiple groups so that weighting
        # can be applied separately to individual areas.
        open_locations = LocationGroup(
            "Open", 10,
            LogicRule(),
            lambda weight: int(weight * 0.2)
        )
        (
            open_locations
            .add_location(Location(TID.TRUCE_MAYOR_1F))
            .add_location(Location(TID.TRUCE_MAYOR_2F))
            .add_location(Location(TID.FOREST_RUINS))
            .add_location(Location(TID.PORRE_MAYOR_2F))
            .add_location(Location(TID.TRUCE_CANYON_1))
            .add_location(Location(TID.TRUCE_CANYON_2))
            .add_location(Location(TID.FIONAS_HOUSE_1))
            .add_location(Location(TID.FIONAS_HOUSE_2))
            .add_location(Location(TID.CURSED_WOODS_1))
            .add_location(Location(TID.CURSED_WOODS_2))
            .add_location(Location(TID.FROGS_BURROW_RIGHT))
        )

        open_keys = LocationGroup("OpenKeys", 5, LogicRule())
        (
            open_keys
            .add_location(Location(TID.ZENAN_BRIDGE_KEY))
            .add_location(Location(TID.SNAIL_STOP_KEY))
            .add_location(Location(TID.LAZY_CARPENTER))
        )

        heckran_locations = LocationGroup("Heckran", 4, LogicRule())
        (
            heckran_locations
            .add_location(Location(TID.HECKRAN_CAVE_SIDETRACK))
            .add_location(Location(TID.HECKRAN_CAVE_ENTRANCE))
            .add_location(Location(TID.HECKRAN_CAVE_1))
            .add_location(Location(TID.HECKRAN_CAVE_2))
            .add_location(Location(TID.TABAN_KEY))
        )

        guardia_castle_locations = LocationGroup(
            "GuardiaCastle", 3, LogicRule()
        )
        (
            guardia_castle_locations
            .add_location(Location(TID.KINGS_ROOM_1000))
            .add_location(Location(TID.QUEENS_ROOM_1000))
            .add_location(Location(TID.KINGS_ROOM_600))
            .add_location(Location(TID.QUEENS_ROOM_600))
            .add_location(Location(TID.ROYAL_KITCHEN))
            .add_location(Location(TID.QUEENS_TOWER_600))
            .add_location(Location(TID.KINGS_TOWER_600))
            .add_location(Location(TID.KINGS_TOWER_1000))
            .add_location(Location(TID.QUEENS_TOWER_1000))
            .add_location(Location(TID.GUARDIA_COURT_TOWER))
        )

        cathedral_locations = LocationGroup(
            "CathedralLocations", 6, LogicRule()
        )
        (
            cathedral_locations
            .add_location(Location(TID.MANORIA_CATHEDRAL_1))
            .add_location(Location(TID.MANORIA_CATHEDRAL_2))
            .add_location(Location(TID.MANORIA_CATHEDRAL_3))
            .add_location(Location(TID.MANORIA_INTERIOR_1))
            .add_location(Location(TID.MANORIA_INTERIOR_2))
            .add_location(Location(TID.MANORIA_INTERIOR_3))
            .add_location(Location(TID.MANORIA_INTERIOR_4))
            .add_location(Location(TID.MANORIA_SHRINE_SIDEROOM_1))
            .add_location(Location(TID.MANORIA_SHRINE_SIDEROOM_2))
            .add_location(Location(TID.MANORIA_BROMIDE_1))
            .add_location(Location(TID.MANORIA_BROMIDE_2))
            .add_location(Location(TID.MANORIA_BROMIDE_3))
            .add_location(Location(TID.MANORIA_SHRINE_MAGUS_1))
            .add_location(Location(TID.MANORIA_SHRINE_MAGUS_2))
            .add_location(Location(TID.YAKRAS_ROOM))
        )

        denadoro_locations = LocationGroup(
            "DenadoroLocations", 6, LogicRule()
        )
        (
            denadoro_locations
            .add_location(Location(TID.DENADORO_MTS_SCREEN2_1))
            .add_location(Location(TID.DENADORO_MTS_SCREEN2_2))
            .add_location(Location(TID.DENADORO_MTS_SCREEN2_3))
            .add_location(Location(TID.DENADORO_MTS_FINAL_1))
            .add_location(Location(TID.DENADORO_MTS_FINAL_2))
            .add_location(Location(TID.DENADORO_MTS_FINAL_3))
            .add_location(Location(TID.DENADORO_MTS_WATERFALL_TOP_1))
            .add_location(Location(TID.DENADORO_MTS_WATERFALL_TOP_2))
            .add_location(Location(TID.DENADORO_MTS_WATERFALL_TOP_3))
            .add_location(Location(TID.DENADORO_MTS_WATERFALL_TOP_4))
            .add_location(Location(TID.DENADORO_MTS_WATERFALL_TOP_5))
            .add_location(Location(TID.DENADORO_MTS_ENTRANCE_1))
            .add_location(Location(TID.DENADORO_MTS_ENTRANCE_2))
            .add_location(Location(TID.DENADORO_MTS_SCREEN3_1))
            .add_location(Location(TID.DENADORO_MTS_SCREEN3_2))
            .add_location(Location(TID.DENADORO_MTS_SCREEN3_3))
            .add_location(Location(TID.DENADORO_MTS_SCREEN3_4))
            .add_location(Location(TID.DENADORO_MTS_AMBUSH))
            .add_location(Location(TID.DENADORO_MTS_SAVE_PT))
            .add_location(Location(TID.DENADORO_MTS_KEY))
        )

        sealed_chest_rule = LogicRule()
        if self.earlyPendant:
            # Access rule is much simpler if early pendant is on
            sealed_chest_rule.add_rule([ItemID.PENDANT])
        else:
            sealed_chest_rule \
                .add_rule([ItemID.PENDANT, ItemID.GATE_KEY, ItemID.DREAMSTONE]) \
                .add_rule([ItemID.PENDANT, ItemID.BENT_SWORD, ItemID.BENT_HILT, Characters.FROG])

        # Sealed locations
        sealed_locations = LocationGroup(
            "SealedLocations", 20,
            sealed_chest_rule,
            lambda weight: int(weight * 0.3))
        (
            sealed_locations
            # Sealed Doors
            .add_location(Location(TID.BANGOR_DOME_SEAL_1))
            .add_location(Location(TID.BANGOR_DOME_SEAL_2))
            .add_location(Location(TID.BANGOR_DOME_SEAL_3))
            .add_location(Location(TID.TRANN_DOME_SEAL_1))
            .add_location(Location(TID.TRANN_DOME_SEAL_2))
            .add_location(Location(TID.ARRIS_DOME_SEAL_1))
            .add_location(Location(TID.ARRIS_DOME_SEAL_2))
            .add_location(Location(TID.ARRIS_DOME_SEAL_3))
            .add_location(Location(TID.ARRIS_DOME_SEAL_4))
            # Sealed chests
            .add_location(Location(TID.TRUCE_INN_SEALED_600))
            .add_location(Location(TID.PORRE_ELDER_SEALED_1))
            .add_location(Location(TID.PORRE_ELDER_SEALED_2))
            .add_location(Location(TID.GUARDIA_CASTLE_SEALED_600))
            .add_location(Location(TID.GUARDIA_FOREST_SEALED_600))
            .add_location(Location(TID.TRUCE_INN_SEALED_1000))
            .add_location(Location(TID.PORRE_MAYOR_SEALED_1))
            .add_location(Location(TID.PORRE_MAYOR_SEALED_2))
            .add_location(Location(TID.GUARDIA_FOREST_SEALED_1000))
            .add_location(Location(TID.GUARDIA_CASTLE_SEALED_1000))
            .add_location(Location(TID.HECKRAN_SEALED_1))
            .add_location(Location(TID.HECKRAN_SEALED_2))
            # Since the blue pyramid only lets you get one of the two chests,
            # set the key item to be in both of them.
            .add_location(
                LinkedLocation(Location(TID.PYRAMID_LEFT),
                               Location(TID.PYRAMID_RIGHT))
            )
        )

        # Sealed chest in the magic cave.
        # Requires both powered up pendant and Magus' Castle access
        magic_cave_locations = LocationGroup(
            "Magic Cave", 4,
            LogicRule().add_rule([
                ItemID.PENDANT,
                ItemID.BENT_SWORD,
                ItemID.BENT_HILT,
                Characters.FROG]))
        (
            magic_cave_locations
            .add_location(Location(TID.MAGIC_CAVE_SEALED))
        )

        # Prehistory
        prehistory_forest_maze_locations = LocationGroup(
            "PrehistoryForestMaze", 18, LogicRule().add_rule([ItemID.GATE_KEY]))
        (
            prehistory_forest_maze_locations
            .add_location(Location(TID.MYSTIC_MT_STREAM))
            .add_location(Location(TID.FOREST_MAZE_1))
            .add_location(Location(TID.FOREST_MAZE_2))
            .add_location(Location(TID.FOREST_MAZE_3))
            .add_location(Location(TID.FOREST_MAZE_4))
            .add_location(Location(TID.FOREST_MAZE_5))
            .add_location(Location(TID.FOREST_MAZE_6))
            .add_location(Location(TID.FOREST_MAZE_7))
            .add_location(Location(TID.FOREST_MAZE_8))
            .add_location(Location(TID.FOREST_MAZE_9))
        )

        prehistory_reptite_locations = LocationGroup(
            "PrehistoryReptite", 27, LogicRule().add_rule([ItemID.GATE_KEY]))
        (
            prehistory_reptite_locations
            .add_location(Location(TID.REPTITE_LAIR_REPTITES_1))
            .add_location(Location(TID.REPTITE_LAIR_REPTITES_2))
            .add_location(Location(TID.REPTITE_LAIR_KEY))
        )

        # Dactyl Nest already has a character, so give it a relatively low
        # weight compared to the other prehistory locations.
        prehistory_dactyl_nest = LocationGroup(
            "PrehistoryDactylNest", 6,
            LogicRule().add_rule([ItemID.GATE_KEY]))
        (
            prehistory_dactyl_nest
            .add_location(Location(TID.DACTYL_NEST_1))
            .add_location(Location(TID.DACTYL_NEST_2))
            .add_location(Location(TID.DACTYL_NEST_3))
        )

        # MelchiorRefinements
        melchiors_refinementslocations = LocationGroup(
            "MelchiorRefinements", 15,
            LogicRule().add_rule([
                ItemID.MOON_STONE,
                ItemID.PRISMSHARD,
                ItemID.GATE_KEY,
                ItemID.PENDANT,
                Characters.MARLE]))
        (
            melchiors_refinementslocations
            .add_location(Location(TID.MELCHIOR_KEY))
        )

        # Frog's Burrow
        frogs_burrow_location = LocationGroup(
            "FrogsBurrowLocation", 9,
            LogicRule().add_rule([ItemID.HERO_MEDAL]))
        (
            frogs_burrow_location
            .add_location(Location(TID.FROGS_BURROW_LEFT))
        )

        # Prehistory
        self.location_groups.append(prehistory_forest_maze_locations)
        self.location_groups.append(prehistory_reptite_locations)
        self.location_groups.append(prehistory_dactyl_nest)

        # Dark Ages
        self.location_groups.append(darkages_locations)

        # 600/1000AD
        self.location_groups.append(fiona_shrine_locations)
        self.location_groups.append(giants_claw_locations)
        self.location_groups.append(northern_ruins_locations)
        self.location_groups.append(northern_ruins_frog_locked)
        self.location_groups.append(guardia_treasury_locations)
        self.location_groups.append(open_locations)
        self.location_groups.append(open_keys)
        self.location_groups.append(heckran_locations)
        self.location_groups.append(cathedral_locations)
        self.location_groups.append(guardia_castle_locations)
        self.location_groups.append(denadoro_locations)
        self.location_groups.append(magic_cave_locations)
        self.location_groups.append(melchiors_refinementslocations)
        self.location_groups.append(frogs_burrow_location)
        self.location_groups.append(early_ozzies_fort_locations)

        # Future
        self.location_groups.append(future_open_locations)
        self.location_groups.append(future_lab_locations)
        self.location_groups.append(future_sewers_locations)
        self.location_groups.append(geno_dome_locations)
        self.location_groups.append(factory_locations)

        # Sealed Locations (chests and doors)
        self.location_groups.append(sealed_locations)

    def init_key_items(self):
        # NOTE:
        # The initial list of key items contains multiples of most of the key
        # items, and not in equal number.  The pendant and gate key are more
        # heavily weighted so that they appear earlier in the run, opening up
        # more potential checks. The ruby knife, dreamstone, clone, and
        # trigger only appear once to reduce the frequency of extremely early
        # go mode from open checks. The hilt and blade show up 2-3 times each,
        # also to reduce early go mode through Magus' Castle to a reasonable
        # number.

        # Seed the list with 5 copies of each item
        # key_item_list = [key for key in (KeyItems)]
        key_item_list = ItemID.get_key_items()

        # key_item_list ends up with 5 of each key item except for
        # late_progression items
        late_progression = [ItemID.RUBY_KNIFE, ItemID.DREAMSTONE,
                            ItemID.CLONE, ItemID.C_TRIGGER]
        key_item_list = [x for x in key_item_list if x not in late_progression]
        key_item_list = 5 * key_item_list
        key_item_list.extend(late_progression)

        # remove some copies of the hilt/blade to reduce early go mode through
        # Magus' Castle
        key_item_list.remove(ItemID.BENT_HILT)
        key_item_list.remove(ItemID.BENT_HILT)
        key_item_list.remove(ItemID.BENT_SWORD)
        key_item_list.remove(ItemID.BENT_SWORD)
        key_item_list.remove(ItemID.BENT_SWORD)

        # Add additional copies of the pendant and gate key
        key_item_list.extend([ItemID.GATE_KEY, ItemID.GATE_KEY, ItemID.GATE_KEY,
                              ItemID.PENDANT, ItemID.PENDANT, ItemID.PENDANT])

        self.keyItemList = key_item_list

    # end init_key_items

    def init_game(self):
        self.game = Game(self.settings, self.config)

    # The ChronoSanityGameConfig wants to remove key item bias after 10 key
    # items are placed.  This just means remove duplicates from the list.
    def update_key_items(self, key_item_list):

        if self.game.get_key_item_count() == 10:
            new_list = []
            for key in key_item_list:
                if key not in new_list:
                    new_list.append(key)
            return new_list
        else:
            return key_item_list


# end ChronosanityGameConfig class


class ChronosanityLostWorldsGameConfig(GameConfig):
    """
    This class represents the game configuration for a
    Lost Worlds Chronosanity game.
    """

    def __init__(self, settings: rset.Settings, config: cfg.RandoConfig):
        self.charLocations = config.char_assign_dict
        GameConfig.__init__(self, settings, config)

    def init_game(self):
        self.game = Game(self.settings, self.config)
        # Test to make sure the settings have LW/CR set?

    def init_key_items(self):
        # Since almost all checks are available from the start, no weighting is
        # being applied to the Lost Worlds key items
        self.keyItemList = [ItemID.C_TRIGGER, ItemID.CLONE, ItemID.PENDANT,
                            ItemID.DREAMSTONE, ItemID.RUBY_KNIFE]

    def init_locations(self):
        # Prehistory
        prehistory_forest_maze_locations = \
            LocationGroup("PrehistoryForestMaze", 10, LogicRule())
        (
            prehistory_forest_maze_locations
            .add_location(Location(TID.MYSTIC_MT_STREAM))
            .add_location(Location(TID.FOREST_MAZE_1))
            .add_location(Location(TID.FOREST_MAZE_2))
            .add_location(Location(TID.FOREST_MAZE_3))
            .add_location(Location(TID.FOREST_MAZE_4))
            .add_location(Location(TID.FOREST_MAZE_5))
            .add_location(Location(TID.FOREST_MAZE_6))
            .add_location(Location(TID.FOREST_MAZE_7))
            .add_location(Location(TID.FOREST_MAZE_8))
            .add_location(Location(TID.FOREST_MAZE_9))
        )

        prehistory_reptite_locations = \
            LocationGroup("PrehistoryReptite", 10, LogicRule())
        (
            prehistory_reptite_locations
            .add_location(Location(TID.REPTITE_LAIR_REPTITES_1))
            .add_location(Location(TID.REPTITE_LAIR_REPTITES_2))
            .add_location(Location(TID.REPTITE_LAIR_KEY))
        )

        # Dactyl Nest already has a character, so give it a relatively low
        # weight compared to the other prehistory locations.
        prehistory_dactyl_nest = \
            LocationGroup("PrehistoryDactylNest", 6, LogicRule())
        (
            prehistory_dactyl_nest
            .add_location(Location(TID.DACTYL_NEST_1))
            .add_location(Location(TID.DACTYL_NEST_2))
            .add_location(Location(TID.DACTYL_NEST_3))
        )

        # Dark Ages
        # Mount Woe does not go away in the randomizer, so it
        # is being considered for key item drops.
        darkages_locations = \
            LocationGroup("Darkages", 10, LogicRule())
        (
            darkages_locations
            .add_location(Location(TID.MT_WOE_1ST_SCREEN))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_1))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_2))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_3))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_4))
            .add_location(Location(TID.MT_WOE_2ND_SCREEN_5))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_1))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_2))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_3))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_4))
            .add_location(Location(TID.MT_WOE_3RD_SCREEN_5))
            .add_location(Location(TID.MT_WOE_FINAL_1))
            .add_location(Location(TID.MT_WOE_FINAL_2))
            .add_location(Location(TID.MT_WOE_KEY))
        )

        # Future
        future_open_locations = \
            LocationGroup("FutureOpen", 10, LogicRule())
        (
            future_open_locations
            # Chests
            .add_location(Location(TID.ARRIS_DOME_RATS))
            .add_location(Location(TID.ARRIS_DOME_FOOD_STORE))
            # KeyItems
            .add_location(Location(TID.ARRIS_DOME_KEY))
            .add_location(Location(TID.SUN_PALACE_KEY))
        )

        future_sewers_locations = \
            LocationGroup("FutureSewers", 8, LogicRule())
        (
            future_sewers_locations
            .add_location(Location(TID.SEWERS_1))
            .add_location(Location(TID.SEWERS_2))
            .add_location(Location(TID.SEWERS_3))
        )

        future_lab_locations = \
            LocationGroup("FutureLabs", 10, LogicRule())
        (
            future_lab_locations
            .add_location(Location(TID.LAB_16_1))
            .add_location(Location(TID.LAB_16_2))
            .add_location(Location(TID.LAB_16_3))
            .add_location(Location(TID.LAB_16_4))
            .add_location(Location(TID.LAB_32_1))
            # Race log chest is not included.
            # .add_location(Location(TID.LAB_32_RACE_LOG))
        )

        geno_dome_locations = \
            LocationGroup("GenoDome", 10, LogicRule())
        (
            geno_dome_locations
            .add_location(Location(TID.GENO_DOME_1F_1))
            .add_location(Location(TID.GENO_DOME_1F_2))
            .add_location(Location(TID.GENO_DOME_1F_3))
            .add_location(Location(TID.GENO_DOME_1F_4))
            .add_location(Location(TID.GENO_DOME_ROOM_1))
            .add_location(Location(TID.GENO_DOME_ROOM_2))
            .add_location(Location(TID.GENO_DOME_PROTO4_1))
            .add_location(Location(TID.GENO_DOME_PROTO4_2))
            .add_location(Location(TID.GENO_DOME_2F_1))
            .add_location(Location(TID.GENO_DOME_2F_2))
            .add_location(Location(TID.GENO_DOME_2F_3))
            .add_location(Location(TID.GENO_DOME_2F_4))
            .add_location(Location(TID.GENO_DOME_KEY))
        )

        factory_locations = \
            LocationGroup("Factory", 10, LogicRule())
        (
            factory_locations
            .add_location(Location(TID.FACTORY_LEFT_AUX_CONSOLE))
            .add_location(Location(TID.FACTORY_LEFT_SECURITY_RIGHT))
            .add_location(Location(TID.FACTORY_LEFT_SECURITY_LEFT))
            .add_location(Location(TID.FACTORY_RUINS_GENERATOR))
            .add_location(Location(TID.FACTORY_RIGHT_DATA_CORE_1))
            .add_location(Location(TID.FACTORY_RIGHT_DATA_CORE_2))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_TOP))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_LEFT))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_BOTTOM))
            .add_location(Location(TID.FACTORY_RIGHT_FLOOR_SECRET))
            .add_location(Location(TID.FACTORY_RIGHT_CRANE_LOWER))
            .add_location(Location(TID.FACTORY_RIGHT_CRANE_UPPER))
            .add_location(Location(TID.FACTORY_RIGHT_INFO_ARCHIVE))
            # .add_location(Location(TID.FACTORY_ROBOT_STORAGE))
            # Inaccessible chest
        )

        # Sealed locations
        sealed_locations = \
            LocationGroup("SealedLocations", 10,
                          LogicRule().add_rule([ItemID.PENDANT]))
        (
            sealed_locations
            # Sealed Doors
            .add_location(Location(TID.BANGOR_DOME_SEAL_1))
            .add_location(Location(TID.BANGOR_DOME_SEAL_2))
            .add_location(Location(TID.BANGOR_DOME_SEAL_3))
            .add_location(Location(TID.TRANN_DOME_SEAL_1))
            .add_location(Location(TID.TRANN_DOME_SEAL_2))
            .add_location(Location(TID.ARRIS_DOME_SEAL_1))
            .add_location(Location(TID.ARRIS_DOME_SEAL_2))
            .add_location(Location(TID.ARRIS_DOME_SEAL_3))
            .add_location(Location(TID.ARRIS_DOME_SEAL_4))
        )

        # 65 Million BC
        self.location_groups.append(prehistory_forest_maze_locations)
        self.location_groups.append(prehistory_reptite_locations)
        self.location_groups.append(prehistory_dactyl_nest)

        # 12000 BC
        self.location_groups.append(darkages_locations)

        # 2300 AD
        self.location_groups.append(future_open_locations)
        self.location_groups.append(future_lab_locations)
        self.location_groups.append(future_sewers_locations)
        self.location_groups.append(geno_dome_locations)
        self.location_groups.append(factory_locations)

        # Sealed Locations (chests and doors)
        self.location_groups.append(sealed_locations)


# end ChronosanityLostWorldsGameConfig class


def apply_epoch_fail(game_config: GameConfig):
    """
    Split and/or add flight requirements to group.  Add JoT to KI list.
    """
    settings = game_config.settings

    if settings.game_mode not in (rset.GameMode.STANDARD,
                                  rset.GameMode.LEGACY_OF_CYRUS,
                                  rset.GameMode.ICE_AGE,
                                  rset.GameMode.VANILLA_RANDO):
        return

    if rset.GameFlags.EPOCH_FAIL not in settings.gameflags:
        return

    flight_tids = (
        # Sun Palace
        TID.SUN_PALACE_KEY,
        # Geno Dome
        TID.GENO_DOME_1F_1, TID.GENO_DOME_1F_2, TID.GENO_DOME_1F_3,
        TID.GENO_DOME_1F_4, TID.GENO_DOME_2F_1, TID.GENO_DOME_2F_2,
        TID.GENO_DOME_2F_3, TID.GENO_DOME_2F_4, TID.GENO_DOME_KEY,
        TID.GENO_DOME_PROTO4_1, TID.GENO_DOME_PROTO4_2,
        TID.GENO_DOME_ROOM_1, TID.GENO_DOME_ROOM_2,
        # Giant's Claw
        TID.GIANTS_CLAW_CAVES_1, TID.GIANTS_CLAW_CAVES_2,
        TID.GIANTS_CLAW_CAVES_3, TID.GIANTS_CLAW_CAVES_4,
        TID.GIANTS_CLAW_CAVES_5, TID.GIANTS_CLAW_KEY,
        TID.GIANTS_CLAW_TRAPS, TID.GIANTS_CLAW_KINO_CELL,
        TID.GIANTS_CLAW_THRONE_1, TID.GIANTS_CLAW_THRONE_2,
        # Northern Ruins
        TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000,
        TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600,
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000,
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600,
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000,
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600,
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000,
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600,
        TID.NORTHERN_RUINS_BASEMENT_1000, TID.NORTHERN_RUINS_BASEMENT_600,
        TID.CYRUS_GRAVE_KEY,
        # Ozzie's Fort
        TID.OZZIES_FORT_FINAL_1, TID.OZZIES_FORT_FINAL_2,
        TID.OZZIES_FORT_GUILLOTINES_1, TID.OZZIES_FORT_GUILLOTINES_2,
        TID.OZZIES_FORT_GUILLOTINES_3, TID.OZZIES_FORT_GUILLOTINES_4,
        # OpenKeys
        TID.LAZY_CARPENTER,
        # MelchiorRefinements
        TID.MELCHIOR_KEY
    )

    new_groups = []
    for group in game_config.location_groups:
        flight_locs = []
        grounded_locs = []
        for location in group.locations:
            if isinstance(location, LinkedLocation):
                tid = location.location1.treasure_id
            else:
                tid = location.treasure_id

            if tid in flight_tids:
                flight_locs.append(location)
            else:
                grounded_locs.append(location)

        if flight_locs:
            if grounded_locs:
                orig_weight = group.weight
                weight_per_loc = orig_weight / len(group.locations)
                for loc in flight_locs:
                    group.remove_location(loc)

                new_name = group.get_name() + '_flight'
                new_weight = ceil(weight_per_loc * len(flight_locs))
                new_rule = copy.deepcopy(group.get_access_rule())
                new_rule.add_requirement([ItemID.JETSOFTIME])
                new_group = LocationGroup(new_name, new_weight, new_rule)
                for flight_loc in flight_locs:
                    new_group.add_location(flight_loc)
                new_groups.append(new_group)
            else:
                group.access_rule = group.get_access_rule().add_requirement([ItemID.JETSOFTIME])

    game_config.location_groups.extend(new_groups)

    # Make sure that JoT gets added to the key item list, and that something
    # gets removed when there's no room.  For now, we're just always going
    # to remove Jerky.  An alternate idea would be to make Jerky a KI check?
    if rset.GameFlags.CHRONOSANITY in settings.gameflags:
        for temp in range(3):
            game_config.keyItemList.append(ItemID.JETSOFTIME)
    else:
        # Vanilla Rando has extra KI spots, and IA has fewer KIs.
        # For other modes, trade out Jerky for Jets

        # LoC has a free KI spot if locked char is on, otherwise it needs
        # something (jerky) removed.
        loc_remove_jerky = (
                settings.game_mode == rset.GameMode.LEGACY_OF_CYRUS and
                rset.GameFlags.LOCKED_CHARS in settings.gameflags
        )

        if settings.game_mode == rset.GameMode.STANDARD or \
                loc_remove_jerky:
            game_config.keyItemList.remove(ItemID.JERKY)

        game_config.keyItemList.append(ItemID.JETSOFTIME)


class NormalGameConfig(GameConfig):
    """
    This class represents the game configuration for a
    Normal game.
    """

    def __init__(self, settings: rset.Settings, config: cfg.RandoConfig):
        self.charLocations = config.char_assign_dict
        self.earlyPendant = rset.GameFlags.FAST_PENDANT in settings.gameflags
        self.lockedChars = rset.GameFlags.LOCKED_CHARS in settings.gameflags
        GameConfig.__init__(self, settings, config)
        apply_epoch_fail(self)

    def init_game(self):
        self.game = Game(self.settings, self.config)

    def init_key_items(self):
        self.keyItemList = ItemID.get_key_items()

    def init_locations(self):
        # Even though treasurewriter *should* give items to each key item spot
        # we're going to still have them be BaselineLocations so that (1) it
        # makes inheritance easier and (2) it makes them always be listed in
        # the spoiler log.
        mid_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.MID_GEAR))
        )

        good_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.GOOD_GEAR))
        )

        high_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.HIGH_GEAR))
        )

        awesome_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.AWESOME_GEAR))
        )

        prehistory_locations = LocationGroup(
            "PrehistoryReptite", 1, LogicRule().add_rule([ItemID.GATE_KEY])
        )
        (
            prehistory_locations
            .add_location(BaselineLocation(TID.REPTITE_LAIR_KEY, high_dist))
        )

        darkages_locations = \
            LocationGroup("Darkages", 1,
                          LogicRule()
                          .add_rule([ItemID.GATE_KEY])
                          .add_rule([ItemID.PENDANT]))
        (
            darkages_locations
            .add_location(BaselineLocation(TID.MT_WOE_KEY, awesome_dist))
        )

        open_keys = LocationGroup(
            "OpenKeys", 5, LogicRule(), lambda weight: weight - 1
        )
        (
            open_keys
            .add_location(BaselineLocation(TID.ZENAN_BRIDGE_KEY, good_dist))
            .add_location(BaselineLocation(TID.SNAIL_STOP_KEY, mid_dist))
            .add_location(BaselineLocation(TID.LAZY_CARPENTER, mid_dist))
            .add_location(BaselineLocation(TID.TABAN_KEY, good_dist))
            .add_location(BaselineLocation(TID.DENADORO_MTS_KEY, good_dist))
        )

        melchiors_refinements_locations = LocationGroup(
            "MelchiorRefinements", 1,
            LogicRule().add_rule([
                ItemID.MOON_STONE,
                ItemID.PRISMSHARD,
                ItemID.GATE_KEY,
                ItemID.PENDANT,
                Characters.MARLE]))
        (
            melchiors_refinements_locations
            .add_location(BaselineLocation(TID.MELCHIOR_KEY, awesome_dist))
        )

        frogs_burrow_location = LocationGroup(
            "FrogsBurrowLocation", 1, LogicRule().add_rule([ItemID.HERO_MEDAL])
        )
        (
            frogs_burrow_location
            .add_location(BaselineLocation(TID.FROGS_BURROW_LEFT, mid_dist))
        )

        guardia_treasury_locations = LocationGroup(
            "GuardiaTreasury", 1, LogicRule().add_rule([ItemID.PRISMSHARD, Characters.MARLE])
        )
        (
            guardia_treasury_locations
            .add_location(BaselineLocation(TID.KINGS_TRIAL_KEY, high_dist))
        )

        giants_claw_locations = LocationGroup(
            "Giantsclaw", 1, LogicRule().add_rule([ItemID.TOMAS_POP])
        )
        (
            giants_claw_locations
            .add_location(BaselineLocation(TID.GIANTS_CLAW_KEY, high_dist))
        )

        fiona_shrine_locations = LocationGroup(
            "Fionashrine", 1, LogicRule().add_rule([Characters.ROBO])
        )
        (
            fiona_shrine_locations
            .add_location(BaselineLocation(TID.FIONA_KEY, high_dist))
        )

        future_keys = LocationGroup(
            "FutureOpen", 3, LogicRule().add_rule([ItemID.PENDANT]),
            lambda weight: weight - 1
        )
        (
            future_keys
            .add_location(BaselineLocation(TID.ARRIS_DOME_KEY, high_dist))
            .add_location(BaselineLocation(TID.SUN_PALACE_KEY, high_dist))
            .add_location(BaselineLocation(TID.GENO_DOME_KEY, awesome_dist))
        )

        # Prehistory
        self.location_groups.append(prehistory_locations)
        # Dark Ages
        self.location_groups.append(darkages_locations)
        # 600/1000
        self.location_groups.append(open_keys)
        self.location_groups.append(melchiors_refinements_locations)
        self.location_groups.append(frogs_burrow_location)
        self.location_groups.append(guardia_treasury_locations)
        self.location_groups.append(giants_claw_locations)
        self.location_groups.append(fiona_shrine_locations)
        # 2300
        self.location_groups.append(future_keys)


# end NormalGameConfig class


class LostWorldsGameConfig(GameConfig):
    """
    This class represents the game configuration for a
    Lost Worlds game.
    """

    def __init__(self, settings: rset.Settings, config: cfg.RandoConfig):
        self.charLocations = config.char_assign_dict
        GameConfig.__init__(self, settings, config)

    def init_game(self):
        self.game = Game(self.settings, self.config)

    def init_key_items(self):
        self.keyItemList = [ItemID.C_TRIGGER, ItemID.CLONE, ItemID.PENDANT,
                            ItemID.DREAMSTONE, ItemID.RUBY_KNIFE]

    def init_locations(self):
        # Not bothering making these baseline locations
        prehistory_locations = LocationGroup(
            "PrehistoryReptite", 1, LogicRule()
        )
        (
            prehistory_locations
            .add_location(Location(TID.REPTITE_LAIR_KEY))
        )

        dark_ages_locations = \
            LocationGroup("Darkages", 1, LogicRule())
        (
            dark_ages_locations
            .add_location(Location(TID.MT_WOE_KEY))
        )

        future_keys = LocationGroup(
            "FutureOpen", 3, LogicRule(),
            lambda weight: weight - 1
        )
        (
            future_keys
            .add_location(Location(TID.ARRIS_DOME_KEY))
            .add_location(Location(TID.SUN_PALACE_KEY))
            .add_location(Location(TID.GENO_DOME_KEY))
        )

        # Prehistory
        self.location_groups.append(prehistory_locations)
        # Dark Ages
        self.location_groups.append(dark_ages_locations)
        # 2300
        self.location_groups.append(future_keys)


# end LostWorldsGameCofig class


class ChronosanityLegacyOfCyrusGameConfig(ChronosanityGameConfig):

    def init_key_items(self):
        ChronosanityGameConfig.init_key_items(self)

        unavail_char = \
            self.config.char_assign_dict[RecruitID.PROTO_DOME].held_char

        removed_items = [
            ItemID.C_TRIGGER, ItemID.CLONE, ItemID.RUBY_KNIFE,
            ItemID.MOON_STONE
        ]

        if unavail_char == Characters.MARLE:
            removed_items.append(ItemID.PRISMSHARD)

        # Compared to normal, there's no reason to remove robo's ribbon b/c
        # there are sufficient key item spots.

        # elif unavail_char == Characters.ROBO:
        #     removed_items.append(ItemID.ROBORIBBON)

        if rset.GameFlags.LOCKED_CHARS not in self.settings.gameflags:
            removed_items.append(ItemID.DREAMSTONE)

        for item_id in removed_items:
            while item_id in self.keyItemList:
                self.keyItemList.remove(item_id)

    def init_locations(self):

        ChronosanityGameConfig.init_locations(self)

        # Remove all future groups.  Remove Ozzie's Fort because it is now
        # an endgame area.
        removed_names = [
            'FutureOpen', 'FutureSewers', 'FutureLabs', 'GenoDome',
            'Factory', 'Ozzie\'s Fort', 'MelchiorRefinements'
        ]

        unavail_char = \
            self.config.char_assign_dict[RecruitID.PROTO_DOME].held_char

        if unavail_char == Characters.MARLE:
            removed_names.append('GuardiaTreasury')
        elif unavail_char == Characters.ROBO:
            removed_names.append('Fionashrine')

        self.remove_location_groups(removed_names)

        sealed_group = self.get_location_group('SealedLocations')
        sealed_group.access_rule = LogicRule().add_rule([ItemID.PENDANT])

        removed_sealed_tids = (
            TID.BANGOR_DOME_SEAL_1, TID.BANGOR_DOME_SEAL_2,
            TID.BANGOR_DOME_SEAL_3, TID.TRANN_DOME_SEAL_1,
            TID.TRANN_DOME_SEAL_2, TID.ARRIS_DOME_SEAL_1,
            TID.ARRIS_DOME_SEAL_2, TID.ARRIS_DOME_SEAL_3,
            TID.ARRIS_DOME_SEAL_4
        )
        sealed_group.remove_location_ti_ds(removed_sealed_tids)

        # Only gate key gives Woe access in LoC
        woe_group = self.get_location_group('Darkages')
        woe_group.access_rule = LogicRule().add_rule([ItemID.GATE_KEY])


class LegacyOfCyrusGameConfig(NormalGameConfig):

    def init_key_items(self):
        NormalGameConfig.init_key_items(self)

        unavail_char = \
            self.config.char_assign_dict[RecruitID.PROTO_DOME].held_char

        removed_items = [
            ItemID.C_TRIGGER, ItemID.CLONE, ItemID.RUBY_KNIFE,
            ItemID.MOON_STONE
        ]

        if unavail_char == Characters.MARLE:
            removed_items.append(ItemID.PRISMSHARD)
        elif unavail_char == Characters.ROBO:
            removed_items.append(ItemID.ROBORIBBON)

        if rset.GameFlags.LOCKED_CHARS not in self.settings.gameflags:
            removed_items.append(ItemID.DREAMSTONE)

        for item in removed_items:
            self.keyItemList.remove(item)

    def init_locations(self):
        # We actually need to mostly redo this whole thing to implement the
        # LoC-specific item distributions.

        good_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.GOOD_GEAR))
        )

        high_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.HIGH_GEAR))
        )

        awesome_dist = td.TreasureDist(
            (1, td.get_item_list(td.ItemTier.AWESOME_GEAR))
        )

        unavail_char = \
            self.config.char_assign_dict[RecruitID.PROTO_DOME].held_char

        prehistory_locations = LocationGroup(
            "PrehistoryReptite", 1, LogicRule().add_rule([ItemID.GATE_KEY])
        )
        (
            prehistory_locations
            .add_location(BaselineLocation(TID.REPTITE_LAIR_KEY, awesome_dist))
        )
        self.location_groups.append(prehistory_locations)

        darkages_locations = \
            LocationGroup("Darkages", 1, LogicRule().add_rule([ItemID.GATE_KEY]))
        (
            darkages_locations
            .add_location(BaselineLocation(TID.MT_WOE_KEY, awesome_dist))
        )
        self.location_groups.append(darkages_locations)

        open_keys = LocationGroup(
            "OpenKeys", 5, LogicRule(), lambda weight: weight - 1
        )
        (
            open_keys
            .add_location(BaselineLocation(TID.ZENAN_BRIDGE_KEY, good_dist))
            .add_location(BaselineLocation(TID.SNAIL_STOP_KEY, good_dist))
            .add_location(BaselineLocation(TID.LAZY_CARPENTER, high_dist))
            .add_location(BaselineLocation(TID.TABAN_KEY, high_dist))
            .add_location(BaselineLocation(TID.DENADORO_MTS_KEY, high_dist))
        )
        self.location_groups.append(open_keys)

        frogs_burrow_location = LocationGroup(
            "FrogsBurrowLocation", 1, LogicRule().add_rule([ItemID.HERO_MEDAL])
        )
        (
            frogs_burrow_location
            .add_location(BaselineLocation(TID.FROGS_BURROW_LEFT, good_dist))
        )
        self.location_groups.append(frogs_burrow_location)

        if unavail_char != Characters.MARLE:
            guardia_treasury_locations = LocationGroup(
                "GuardiaTreasury", 1, LogicRule().add_rule([Characters.MARLE, ItemID.PRISMSHARD])
            )
            (
                guardia_treasury_locations
                .add_location(BaselineLocation(TID.KINGS_TRIAL_KEY,
                                               awesome_dist))
            )
            self.location_groups.append(guardia_treasury_locations)

        giants_claw_locations = LocationGroup(
            "Giantsclaw", 1, LogicRule().add_rule([ItemID.TOMAS_POP])
        )
        (
            giants_claw_locations
            .add_location(BaselineLocation(TID.GIANTS_CLAW_KEY, awesome_dist))
        )
        self.location_groups.append(giants_claw_locations)

        if unavail_char != Characters.ROBO:
            fiona_shrine_locations = LocationGroup(
                "Fionashrine", 1, LogicRule().add_rule([Characters.ROBO])
            )
            (
                fiona_shrine_locations
                .add_location(BaselineLocation(TID.FIONA_KEY, awesome_dist))
            )
            self.location_groups.append(fiona_shrine_locations)


class IceAgeGameConfig(NormalGameConfig):
    def __init__(self, settings: rset.Settings, config: cfg.RandoConfig):
        NormalGameConfig.__init__(self, settings, config)

    def init_game(self):
        NormalGameConfig.init_game(self)

    def init_key_items(self):
        NormalGameConfig.init_key_items(self)

        # Remove other go-mode items.  These will be replaced with gear as
        # they would be in Chronosanity modes
        removed_items = [
            ItemID.C_TRIGGER, ItemID.CLONE, ItemID.RUBY_KNIFE
        ]

        for item in removed_items:
            self.keyItemList.remove(item)

    def init_locations(self):
        NormalGameConfig.init_locations(self)

        # The only change needed is that Woe will not be accessible except
        # when dreamstone, ayla, and dactyl char are present.  We keep the
        # group around because a (dud) key item still gets placed there.
        woe_group = next(
            x for x in self.location_groups if x.name == 'Darkages'
        )

        woe_group.access_rule = LogicRule().add_rule([ItemID.GATE_KEY, ItemID.DREAMSTONE, Characters.AYLA])


class ChronosanityIceAgeGameConfig(ChronosanityGameConfig):

    def init_key_items(self):
        ChronosanityGameConfig.init_key_items(self)

        # Remove other go-mode items.  These will be replaced with gear as
        # they would be in Chronosanity modes
        removed_items = [
            ItemID.C_TRIGGER, ItemID.CLONE, ItemID.RUBY_KNIFE
        ]

        for item_id in removed_items:
            while item_id in self.keyItemList:
                self.keyItemList.remove(item_id)

    def init_locations(self):
        ChronosanityGameConfig.init_locations(self)

        # For Chronosanity, just remove the Woe group.
        self.location_groups.remove(self.get_location_group('Darkages'))

# TODO: Delete these
# Note: Accessing MtWoe is the same as accessing EoT in current logic.
#       This means you can grind for levels if you really need it.
# def _can_access_giants_claw_vr(game: Game):
#     return (
#             game.has_key_item(ItemID.TOMAS_POP) and
#             game.canAccessMtWoe()
#     )
#
#
# def _can_access_kings_trial_vr(game: Game):
#     return (
#             game.has_character(Characters.MARLE) and
#             game.has_key_item(ItemID.PRISMSHARD) and
#             game.canAccessMtWoe()
#     )
#
#
# def _can_access_fionas_shrine_vr(game: Game):
#     return (
#             game.has_character(Characters.ROBO) and
#             game.canAccessMtWoe()
#     )
#
#
# def _can_access_northern_ruins_vr(game: Game):
#     return game.has_key_item(ItemID.TOOLS)
#
#
# def _can_access_cyrus_grave_vr(game: Game):
#     return (
#             _can_access_northern_ruins_vr(game) and
#             game.has_character(Characters.FROG) and
#             game.canAccessMtWoe()
#     )


_awesome_gear_dist = td.TreasureDist(
    (1, td.get_item_list(td.ItemTier.AWESOME_GEAR))
)


class VanillaRandoGameConfig(NormalGameConfig):

    def init_key_items(self):
        NormalGameConfig.init_key_items(self)

        self.keyItemList.append(ItemID.TOOLS)
        self.keyItemList.remove(ItemID.ROBORIBBON)

    def init_locations(self):
        NormalGameConfig.init_locations(self)

        can_access_woe = LogicRule().add_rule([ItemID.PENDANT]).add_rule([ItemID.GATE_KEY])

        # Gate the endgame quests behind EOT (Mt. Woe) access.
        giants_claw = self.get_location_group('Giantsclaw')
        giants_claw.access_rule = copy.deepcopy(can_access_woe).add_requirement([ItemID.TOMAS_POP])

        kings_trial = self.get_location_group('GuardiaTreasury')
        kings_trial.access_rule = \
            copy.deepcopy(can_access_woe).add_requirement([ItemID.PRISMSHARD, Characters.MARLE])

        fiona_shrine = self.get_location_group('Fionashrine')
        fiona_shrine.access_rule = copy.deepcopy(can_access_woe).add_requirement([Characters.ROBO])

        bekkler_key = LocationGroup(
            "BekklersLab", 1,
            LogicRule().add_rule([ItemID.C_TRIGGER])
        )
        bekkler_key.add_location(
            BaselineLocation(TID.BEKKLER_KEY, _awesome_gear_dist)
        )
        self.location_groups.append(bekkler_key)

        cyrus_key = LocationGroup(
            "HerosGrave", 1, copy.deepcopy(can_access_woe).add_requirement([ItemID.TOOLS, Characters.FROG])
        )
        cyrus_key.add_location(
            BaselineLocation(TID.CYRUS_GRAVE_KEY, _awesome_gear_dist)
        )
        self.location_groups.append(cyrus_key)


class ChronosanityVanillaRandoGameConfig(ChronosanityGameConfig):

    def init_key_items(self):
        ChronosanityGameConfig.init_key_items(self)

        for i in range(5):
            self.keyItemList.append(ItemID.TOOLS)

        while ItemID.ROBORIBBON in self.keyItemList:
            self.keyItemList.remove(ItemID.ROBORIBBON)

    def init_locations(self):
        ChronosanityGameConfig.init_locations(self)

        can_access_woe = LogicRule().add_rule([ItemID.PENDANT]).add_rule([ItemID.GATE_KEY])
        giants_claw = self.get_location_group('Giantsclaw')
        giants_claw.access_rule = copy.deepcopy(can_access_woe).add_requirement([ItemID.TOMAS_POP])

        kings_trial = self.get_location_group('GuardiaTreasury')
        kings_trial.access_rule = copy.deepcopy(can_access_woe).add_requirement([ItemID.PRISMSHARD, Characters.MARLE])

        fiona_shrine = self.get_location_group('Fionashrine')
        fiona_shrine.access_rule = copy.deepcopy(can_access_woe).add_requirement([Characters.ROBO])

        bekkler_key = LocationGroup(
            "BekklersLab", 2,
            LogicRule().add_rule([ItemID.C_TRIGGER])
        )
        bekkler_key.add_location(Location(TID.BEKKLER_KEY))

        self.location_groups.append(bekkler_key)

        northern_ruins_locations = self.get_location_group('NorthernRuins')
        northern_ruins_locations.access_rule = copy.deepcopy(can_access_woe).add_requirement([ItemID.TOOLS])

        northern_ruins_frog = self.get_location_group('NorthernRuinsFrogLocked')
        northern_ruins_frog.add_location(Location(TID.CYRUS_GRAVE_KEY))
        northern_ruins_frog.access_rule = \
            copy.deepcopy(can_access_woe).add_requirement([ItemID.TOOLS, Characters.FROG])


def get_game_config(settings: rset.Settings, config: cfg.RandoConfig) -> GameConfig:
    """
    Get a GameConfig object based on randomizer flags.
    The GameConfig object will have the correct locations,
    initial key items, and game setup for the selected flags.

    :param settings: An rset.Settings object containing flag choices
    :param config: A cfg.RandoConfig object containing randomizer assignments

    :return: A GameConfig object appropriate for the given flag set
    """

    # Maybe each game mode needs to supply its own logic setup function.
    # Why should this file need to be aware of every possible game mode?
    chronosanity = rset.GameFlags.CHRONOSANITY in settings.gameflags
    standard = rset.GameMode.STANDARD == settings.game_mode
    lost_worlds = rset.GameMode.LOST_WORLDS == settings.game_mode
    ice_age = rset.GameMode.ICE_AGE == settings.game_mode
    legacy_of_cyrus = rset.GameMode.LEGACY_OF_CYRUS == settings.game_mode
    vanilla = rset.GameMode.VANILLA_RANDO == settings.game_mode

    if chronosanity:
        if lost_worlds:
            cfg_type = ChronosanityLostWorldsGameConfig
        elif legacy_of_cyrus:
            cfg_type = ChronosanityLegacyOfCyrusGameConfig
        elif ice_age:
            cfg_type = ChronosanityIceAgeGameConfig
        elif vanilla:
            cfg_type = ChronosanityVanillaRandoGameConfig
        elif standard:
            cfg_type = ChronosanityGameConfig
        else:
            raise ValueError('Invalid Game Mode')
    else:
        if lost_worlds:
            cfg_type = LostWorldsGameConfig
        elif legacy_of_cyrus:
            cfg_type = LegacyOfCyrusGameConfig
        elif ice_age:
            cfg_type = IceAgeGameConfig
        elif vanilla:
            cfg_type = VanillaRandoGameConfig
        elif standard:
            cfg_type = NormalGameConfig
        else:
            raise ValueError('Invalid Game Mode')

    return cfg_type(settings, config)
# end get_game_config
