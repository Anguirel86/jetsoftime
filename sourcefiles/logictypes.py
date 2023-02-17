from __future__ import annotations
import typing

from ctenums import ItemID, CharID, RecruitID, TreasureID
import treasuredata as td
import randosettings as rset
import randoconfig as cfg
#
# This file holds various classes/types used by the logic placement code.
#


class Game:
    """
    The Game class is used to keep track of game state
    as the randomizer places key items.  It:
      - Tracks key items obtained
      - Tracks characters obtained
      - Keeps track of user selected flags
      - Provides logic convenience functions
    """

    def __init__(self, settings: rset.Settings,
                 config: cfg.RandoConfig):
        self.characters = set()
        self.key_items = set()
        self.early_pendant = rset.GameFlags.FAST_PENDANT in settings.gameflags
        self.locked_chars = rset.GameFlags.LOCKED_CHARS in settings.gameflags
        self.lost_worlds = rset.GameMode.LOST_WORLDS == settings.game_mode
        self.char_locations = config.char_assign_dict
        self.legacy_of_cyrus = \
            rset.GameMode.LEGACY_OF_CYRUS == settings.game_mode

        # In case we need to look something else up
        self.settings = settings

    def get_key_item_count(self):
        """
        Get the number of key items that have been acquired by the player.

        :return: Number of obtained key items
        """
        return len(self.key_items)

    def has_character(self, character: CharID) -> bool:
        """
        Check if the player has the specified character

        :param character: Name of a character
        :return: true if the character has been acquired, false if not
        """
        return character in self.characters

    def add_character(self, character: CharID):
        """
        Add a character to the set of characters acquired.

        :param character: The character to add
        """
        self.characters.add(character)

    def remove_character(self, character: CharID):
        """
        Remove a character from the set of characters acquired.

        :param character: The character to remove
        """
        self.characters.discard(character)

    def has_key_item(self, item: ItemID) -> bool:
        """
        Check if the player has a given key item.

        :param item: The key item to check for
        :return: True if the player has the key item, false if not
        """
        return item in self.key_items

    def add_key_item(self, item: ItemID):
        """
        Add a key item to the set of key items acquired.

        :param item: The Key Item to add
        """
        self.key_items.add(item)

    def remove_key_item(self, item: ItemID):
        """
        Remove a key item from the set of key items acquired.

        :param item: The Key Item to remove
        """
        self.key_items.discard(item)

    def update_available_characters(self):
        """
        Determine which characters are available based on what key items/time
        periods are available to the player.
        """

        # charLocations is a dictionary from cfg.RandoConfig whose keys come
        # from ctenums.RecruitID.  The corresponding value gives the held
        # character in a held_char field

        # Empty the set just in case the placement algorithm had to
        # backtrack and a character is no longer available.
        self.characters.clear()

        if rset.GameFlags.STARTERS_SUFFICIENT in self.settings.gameflags and \
           self.settings.game_mode == rset.GameMode.STANDARD:
            self.add_character(
                self.char_locations[RecruitID.STARTER_1].held_char
            )
            self.add_character(
                self.char_locations[RecruitID.STARTER_2].held_char
            )

            # You have to add the other characters eventually or else the
            # logic will stall out.
            if self._can_access_black_omen() and self._can_access_tyrano_lair() and \
               self.has_key_item(ItemID.RUBY_KNIFE):
                self.add_character(
                    self.char_locations[RecruitID.CATHEDRAL].held_char
                )
                self.add_character(
                    self.char_locations[RecruitID.CASTLE].held_char
                )
                self.add_character(
                    self.char_locations[RecruitID.PROTO_DOME].held_char
                )
                self.add_character(
                    self.char_locations[RecruitID.DACTYL_NEST].held_char
                )
                self.add_character(
                    self.char_locations[RecruitID.FROGS_BURROW].held_char
                )
            return

        # The first four characters are always available.
        self.add_character(self.char_locations[RecruitID.STARTER_1].held_char)
        self.add_character(self.char_locations[RecruitID.STARTER_2].held_char)
        self.add_character(self.char_locations[RecruitID.CATHEDRAL].held_char)
        self.add_character(self.char_locations[RecruitID.CASTLE].held_char)

        # The remaining three characters are progression gated.
        if self._can_access_future():
            self.add_character(
                self.char_locations[RecruitID.PROTO_DOME].held_char
            )
        if self._can_access_dactyl_character():
            self.add_character(
                self.char_locations[RecruitID.DACTYL_NEST].held_char
            )
        if self._has_masamune():
            self.add_character(
                self.char_locations[RecruitID.FROGS_BURROW].held_char
            )
    # end update_available_characters function

    def _can_access_dactyl_character(self):
        # If character locking is on, dreamstone is required to get the
        # Dactyl Nest character in addition to prehistory access.
        return (self._can_access_prehistory() and
                ((not self.locked_chars) or
                 self.has_key_item(ItemID.DREAMSTONE)))

    def _can_access_future(self):
        return not self.legacy_of_cyrus and \
               (self.has_key_item(ItemID.PENDANT) or self.lost_worlds)

    def _can_access_prehistory(self):
        return self.has_key_item(ItemID.GATE_KEY) or self.lost_worlds

    def _can_access_tyrano_lair(self):
        return self._can_access_prehistory() and \
            self.has_key_item(ItemID.DREAMSTONE)

    def _has_masamune(self):
        return (self.has_key_item(ItemID.BENT_HILT) and
                self.has_key_item(ItemID.BENT_SWORD))

    def _can_access_black_omen(self):
        return (self._can_access_future() and
                self.has_key_item(ItemID.CLONE) and
                self.has_key_item(ItemID.C_TRIGGER))
    # End Game class


class LogicRule:
    """
    This class holds logical access rules for a LocationGroup.
    """
    def __init__(self):
        self.rules = []
        pass

    def add_rule(self, rule: list[typing.Union[ItemID, CharID]]):
        """
        Add a rule to this object.
        Rules are a list of item or character IDs that block access to a location.

        :param rule: List of items or characters needed to access a location
        :return: A reference to this object
        """
        self.rules.append(rule)
        return self

    def get_multiworld_rule(self):
        """
        Get this access rule in a format suitable for the multiworld yaml.
        """
        pass

    def add_requirement(self, new_rule: list[typing.Union[ItemID, CharID]]):
        """
        Extend an existing rule with a new set of requirements.

        :param new_rule: new rule to append to the existing rules
        """
        if len(self.rules) == 0:
            self.add_rule(new_rule)
        else:
            for rule in self.rules:
                rule.extend(new_rule)

    def __call__(self, game: Game) -> bool:
        """
        Evaluate this set of rules to see if a location group is accessible.

        :param game: Game object with current game state
        :return: True if the location is accessible, false if not
        """
        if len(self.rules) == 0:
            # Empty rules list means this is a sphere 0 check
            return True

        for rule in self.rules:

            can_access = True
            for requirement in rule:
                has_char = game.has_character(requirement) if type(requirement) == type(CharID) else False
                has_key = game.has_key_item(requirement) if type(requirement) == type(ItemID) else False
                if not (has_char or has_key):
                    can_access = False
                    break

            if can_access:
                return True

        return False


class Location:
    """
    This class represents a location within the game.
    It is the parent class for the different location types
    """

    def __init__(self, treasure_id: TreasureID):
        self.treasure_id = treasure_id
        self.key_item = None

    def _jot_json(self):
        return {self.get_name(): str(self.get_key_item())}

    def get_name(self) -> str:
        """
        Get the name of this location.

        :return: The name of this location
        """
        return str(self.treasure_id)

    def set_key_item(self, key_item: ItemID):
        """
        Set the key item at this location.

        :param key_item: The key item to be placed at this location
        """
        self.key_item = key_item

    def get_key_item(self) -> ItemID:
        """
        Get the key item placed at this location.

        :return: The key item being held in this location
        """
        return self.key_item

    def unset_key_item(self):
        """
        Unset the key item from this location.
        """
        self.key_item = None

    def has_tid(self, treasure_id: TreasureID) -> bool:
        """
        Determine whether the location holds the given TID

        :param treasure_id: The treasureID to check against this location's treasure
        :return: True if this location contains the given treasure, false if not
        """
        return self.treasure_id == treasure_id

    def write_key_item(self, config: cfg.RandoConfig):
        """
        Write the key item set to this location to a RandoConfig object
        :param config: The RandoConfig object which holds the
                       treasure assignment dictionary
        """
        config.treasure_assign_dict[self.treasure_id].held_item = self.key_item

    def lookup_key_item(self, config: cfg.RandoConfig) -> ItemID:
        """
        Use the given config to see what is currently assigned to this location.

        :param config: The RandoConfig object which holds the
                       treasure assignment dictionary
        """
        return config.treasure_assign_dict[self.treasure_id].held_item

# End Location class


class BaselineLocation(Location):
    """
    The randomizer assigns a treasure to each location, even key item locations.
    Some game modes may choose to define special rules for some locations.

    The BaselineLocation class allows a location to be augmented with a treasure
    distribution (treasuredata.TreasureDist) which determines how an item should
    be assigned to it in the event that a key item assignment is not made.
    """

    def __init__(self, treasure_id: TreasureID,
                 loot_dist: td.TreasureDist):
        Location.__init__(self, treasure_id)
        self.loot_dist = loot_dist

    def get_treasure_dist(self) -> td.TreasureDist:
        """
        Get the treasure distribution associated with this check.

        :return: The treasure distribution associated with this check
        """
        return self.loot_dist

    def set_treasure_dist(self, loot_dist: td.TreasureDist):
        """
        Set the treasure distribution associated with this check.

        :param loot_dist: The treasure distribution to associate with this check
        """
        self.loot_dist = loot_dist

    def write_random_item(self, config: cfg.RandoConfig):
        """
        Use this object's treasure distribution to write a random item to then
        given config.  Also sets this object's key item to the chosen item.

        :param config: The cfg.RandoConfig to write the item to
        """
        item = self.loot_dist.get_random_item()
        self.write_treasure(item, config)

    def write_treasure(self, treasure: ItemID, config: cfg.RandoConfig):
        """
        Write the given item to the given config.  Also sets this object's
        key item to the chosen item.

        :param treasure: The ItemID to write
        :param config: The cfg.RandoConfig to write the ItemID to
        """
        config.treasure_assign_dict[self.treasure_id].held_item = treasure
        self.set_key_item(treasure)
# End BaselineLocation class


class LinkedLocation:
    """
    This class represents a set of linked locations.  The key item will
    be set in both of the locations.  This is used for the blue pyramid
    where there are two chests but the player can only get one.

    Decided not to have LinkedLocation inherit from Location.
    Location is a TID with an item assignment, but there are no TIDs to assign
    to the linked locations.
    Just make it implement the same behavior as Location.
    """
    def __init__(self, location1: Location, location2: Location):
        self.location1 = location1
        self.location2 = location2

    def _jot_json(self):
        return {self.get_name(): str(self.get_key_item())}

    def get_name(self):
        return (f"Linked: {self.location1.get_name()} + "
                f"{self.location2.get_name()}")

    def set_key_item(self, key_item):
        """
        Set the key item for both locations in this linked location.

        @param key_item: Key item to set to the linked locations
        """
        self.location1.set_key_item(key_item)
        self.location2.set_key_item(key_item)

    def get_key_item(self):
        """
        Get the key item placed at this location.

        :return: The key item being held in this location
        """
        if self.location1.get_key_item() == self.location2.get_key_item():
            return self.location1.key_item
        else:
            raise ValueError('Linked locations do not match.')

    def unset_key_item(self):
        """
        Unset the key item from this location.
        """
        self.location1.unset_key_item()
        self.location2.unset_key_item()

    def write_key_item(self, config: cfg.RandoConfig):
        """
        Write the key item to both of the linked locations.

        @param config: Config to write this location's item to
        """
        self.location1.write_key_item(config)
        self.location2.write_key_item(config)

    def lookup_key_item(self, config: cfg.RandoConfig) -> ItemID:
        """
        Use the given config to see what is currently assigned to this location.
        Since this is meant to be a lookup of a key item, this will raise a
        ValueError if the linked locations do not hold identical items.

        :param config: The randoconfig.RandoConfig object which holds the
                       treasure assignment dictionary
        :return: The key item assigned to this location
        :raises ValueError: When the linked locations are assigned different items
        """
        item1 = self.location1.lookup_key_item(config)
        item2 = self.location2.lookup_key_item(config)

        if item1 != item2:
            raise ValueError(
                'LinkedLocation has two different items assigned.'
            )
        else:
            return item1

    def has_tid(self, treasure_id: TreasureID) -> bool:
        """
        Determine whether the location holds the given TID.

        @param treasure_id: Treasure location to validate against this location's treasure
        @return: True if treasures match, false if not
        """
        return (self.location1.has_tid(treasure_id) or
                self.location2.has_tid(treasure_id))
# end LinkedLocation class


class LocationGroup:
    """
    This class represents a group of locations controlled by
    the same access rule.
    """

    def __init__(self,
                 name: str,
                 weight: int,
                 access_rule: LogicRule,
                 weight_decay: typing.Callable[[int], int] = None):
        """
        Constructor for a LocationGroup.

        :param name: The name of this LocationGroup
        :param weight: The initial weighting factor of this LocationGroup
        :param access_rule: A function used to determine if this LocationGroup
                            is accessible
        :param weight_decay: Optional function to define weight decay of this
                             LocationGroup
        """
        self.name: str = name
        self.locations: list[Location] = []
        self.weight: int = weight
        self.access_rule: LogicRule = access_rule
        self.weight_decay: typing.Callable[[int], int] = weight_decay
        self.weight_stack: list[int] = []

    def can_access(self, game):
        """
        Return whether this location group is logically accessible.

        :param game: The game object with current game state
        :return: True if this location is accessible, false if not
        """
        return self.access_rule(game)

    def get_access_rule(self) -> LogicRule:
        """
        Return a reference to the access rule used for this location.
        :return: LogicRule used by this location
        """
        return self.access_rule

    def get_name(self) -> str:
        """
        Get the name of this location group.
        :return: The name of this location as a string
        """
        return self.name

    def get_weight(self) -> int:
        """
        Get the weight value being used to select locations from this group.

        :return: Weight value used by this location group
        """
        return self.weight

    def set_weight(self, weight: int):
        """
        Set the weight used when selecting locations from this group.
        The weight cannot be set less than 1.

        :param weight: Weight value to set
        """
        if weight < 1:
            weight = 1
        self.weight = weight

    def decay_weight(self):
        """
        This function is used to decay the weight value of this
        LocationGroup when a location is chosen from it.
        """
        self.weight_stack.append(self.weight)
        if self.weight_decay is None:
            # If no weight decay function was given, reduce the weight of this
            # LocationGroup to 1 to make it unlikely to get any other items.
            self.set_weight(1)
        else:
            self.set_weight(self.weight_decay(self.weight))

    def undo_weight_decay(self):
        """
        Undo a previous weight decay of this LocationGroup.
        The previous weight values are stored in the weightStack.
        """
        if len(self.weight_stack) > 0:
            self.set_weight(self.weight_stack.pop())

    def restore_initial_weight(self):
        """
        Undo all weight decay of this LocationGroup.
        """
        if self.weight_stack:
            self.set_weight(self.weight_stack[0])
            self.weight_stack = []

    def get_available_location_count(self) -> int:
        """
        Get the number of available locations in this group.

        :return: The number of locations in this group
        """
        return len(self.locations)

    def add_location(self, location):
        """
        Add a location to this location group. If the location is
        already part of this location group then nothing happens.

        :param location: A location object to add to this location group
        """
        if location not in self.locations:
            self.locations.append(location)
        return self

    def remove_location(self, location):
        """
        Remove a location from this group.

        :param location: Location to remove from this group
        """
        self.locations.remove(location)

    def remove_location_ti_ds(
            self,
            removed_treasure_ids: typing.Union[TreasureID,
                                               typing.Iterable[TreasureID]]):
        """
        Remove a location with the given TreasureID from this group
        :param removed_treasure_ids: TreasureID to remove from this group or an iterable
                                     of TreasureIDs to remove
        """
        if isinstance(removed_treasure_ids, TreasureID):
            removed_treasure_ids = [removed_treasure_ids]

        remove_locs = []
        for loc in self.locations:
            for tid in removed_treasure_ids:
                if loc.has_tid(tid):
                    remove_locs.append(loc)
                    break

        for loc in remove_locs:
            self.locations.remove(loc)

    def get_locations(self) -> list[Location]:
        """
        Get a list of all locations that are part of this location group.
        @return: List of locations associated with this LocationGroup
        """
        return self.locations.copy()

    def has_location(self, location: Location) -> bool:
        """
        Check if this group has a given location.
        """
        for loc in self.locations:
            if loc.get_name() == location.get_name():
                return True
        return False
# End LocationGroup class
