import copy
import dataclasses
import enum
import math
import re
import typing

import collision
import format
import messages
from messages import ItemFlags


class CollectSound(enum.Enum):
    HP15 = b'items/r_item1.wav'
    HP25 = b'items/health1.wav'
    HP100 = b'items/r_item2.wav'
    ARMOR = b'items/armor1.wav'
    AMMO = b'weapons/lock4.wav'
    WEAPON = b'weapons/pkup.wav'

COLLECT_SOUNDS = [x.value for x in CollectSound]


MIN_HEALTH = 1
MAX_HEALTH = 100
MAX_MEGAHEALTH = 250
MIN_SHELLS = 0
MAX_SHELLS = 100
MIN_NAILS = 0
MAX_NAILS = 200
MIN_ROCKETS = 0
MAX_ROCKETS = 100
MIN_CELLS = 0
MAX_CELLS = 100

@dataclasses.dataclass
class Health:
    name = 'health'
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        if items & ItemFlags.SUPERHEALTH:
            return min(value, MAX_MEGAHEALTH)
        else:
            return min(value, MAX_HEALTH)

@dataclasses.dataclass
class Shells:
    name = 'shells'
    min = MIN_SHELLS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_SHELLS)

@dataclasses.dataclass
class Nails:
    name = 'nails'
    min = MIN_NAILS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_NAILS)

@dataclasses.dataclass
class Rockets:
    name = 'rockets'
    min = MIN_ROCKETS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_ROCKETS)

@dataclasses.dataclass
class Cells:
    name = 'cells'
    min = MIN_CELLS
    value: int
    @staticmethod
    def bound(value: int, items: ItemFlags) -> int:
        return min(value, MAX_CELLS)

@dataclasses.dataclass
class Armor:
    value: int

@dataclasses.dataclass
class Item:
    value: ItemFlags

# Convenience wrapper around ClientStats to be able to access it dynamically
# with above stat types
class ClientStatsAccessor(format.ClientStats):
    def __init__(self, data: format.ClientStats):
        super().__init__(data.items, data.health, data.armor, data.shells,
                         data.nails, data.rockets, data.cells,
                         data.activeweapon, data.ammo)
    def __getitem__(self, stat_type):
        return getattr(self, stat_type.name)
    def __setitem__(self, stat_type, value):
        setattr(self, stat_type.name, value)


def get_damage_reduction(items: ItemFlags) -> float:
    damage_reduction = 0.0
    if items & ItemFlags.ARMOR1:
        damage_reduction = 0.3
    elif items & ItemFlags.ARMOR2:
        damage_reduction = 0.6
    elif items & ItemFlags.ARMOR3:
        damage_reduction = 0.8
    return damage_reduction

def lost_armor_bounds(damage_ceiled: float, armor: int, reduction: float):
    assert damage_ceiled == math.ceil(damage_ceiled)
    damage_floored = damage_ceiled - 1.0
    lost_armor_lower_bound = min(armor, math.ceil(reduction * damage_floored))
    lost_armor_upper_bound = min(armor, math.ceil(reduction * damage_ceiled))
    return lost_armor_lower_bound, lost_armor_upper_bound


class CollectableHealth15:
    gives = [Health(15)]
    collect_sound = CollectSound.HP15
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 15 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableHealth25:
    gives = [Health(25)]
    collect_sound = CollectSound.HP25
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 25 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.health < MAX_HEALTH
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableHealth100:
    gives = [Item(ItemFlags.SUPERHEALTH), Health(100)]
    collect_sound = CollectSound.HP100
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You receive 100 health\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return True
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableShells20:
    gives = [Shells(20)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableShells40:
    gives = [Shells(40)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the shells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.shells < MAX_SHELLS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableNails25:
    gives = [Nails(25)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableNails50:
    gives = [Nails(50)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the nails\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.nails < MAX_NAILS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableRockets5:
    gives = [Rockets(5)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableRockets10:
    gives = [Rockets(10)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the rockets\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.rockets < MAX_ROCKETS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableCells6:
    gives = [Cells(6)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableCells12:
    gives = [Cells(12)]
    collect_sound = CollectSound.AMMO
    mins, maxs = [0.0, 0.0, 0.0], [32.0, 32.0, 56.0]
    print_text = b"You got the cells\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return stats.cells < MAX_CELLS
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableGreenArmor:
    armor_value = 100
    gives = [Item(ItemFlags.ARMOR1), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR1) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableYellowArmor:
    armor_value = 150
    gives = [Item(ItemFlags.ARMOR2), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR2) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableRedArmor:
    armor_value = 200
    gives = [Item(ItemFlags.ARMOR3), Armor(armor_value)]
    collect_sound = CollectSound.ARMOR
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got armor\n"

    @classmethod
    def will_collect(cls, stats, is_coop):
        return (get_damage_reduction(ItemFlags.ARMOR3) * cls.armor_value >=
                get_damage_reduction(stats.items) * stats.armor)
    @staticmethod
    def will_disappear(stats, is_coop):
        return True

class CollectableSuperShotgun:
    gives = [Item(ItemFlags.SUPER_SHOTGUN), Shells(5)]
    collect_sound = CollectSound.WEAPON
    print_text = b"You got the Double-barrelled Shotgun\n"
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_SHOTGUN)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

class CollectableNailgun:
    gives = [Item(ItemFlags.NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.NAILGUN)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

class CollectableSuperNailgun:
    gives = [Item(ItemFlags.SUPER_NAILGUN), Nails(30)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Super Nailgun\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.SUPER_NAILGUN)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

class CollectableGrenadeLauncher:
    gives = [Item(ItemFlags.GRENADE_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Grenade Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.GRENADE_LAUNCHER)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

class CollectableRocketLauncher:
    gives = [Item(ItemFlags.ROCKET_LAUNCHER), Rockets(5)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Rocket Launcher\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.ROCKET_LAUNCHER)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

class CollectableLightningGun:
    gives = [Item(ItemFlags.LIGHTNING), Cells(15)]
    collect_sound = CollectSound.WEAPON
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]
    print_text = b"You got the Thunderbolt\n"

    @staticmethod
    def will_collect(stats, is_coop):
        return not is_coop or not (stats.items & ItemFlags.LIGHTNING)
    @staticmethod
    def will_disappear(stats, is_coop):
        return not is_coop

@dataclasses.dataclass
class CollectableBackpack:
    gives = []
    collect_sound = CollectSound.AMMO
    mins, maxs = [-16.0, -16.0, 0.0], [16.0, 16.0, 56.0]

    @staticmethod
    def will_collect(stats, is_coop):
        return True
    @staticmethod
    def will_disappear(stats, is_coop):
        return True


COLLECTABLE_MODELS_MAP = {
    b'maps/b_bh10.bsp': CollectableHealth15,
    b'maps/b_bh25.bsp': CollectableHealth25,
    b'maps/b_bh100.bsp': CollectableHealth100,
    b'maps/b_shell0.bsp': CollectableShells20,
    b'maps/b_shell1.bsp': CollectableShells40,
    b'maps/b_nail0.bsp': CollectableNails25,
    b'maps/b_nail1.bsp': CollectableNails50,
    b'maps/b_rock0.bsp': CollectableRockets5,
    b'maps/b_rock1.bsp': CollectableRockets10,
    b'maps/b_batt0.bsp': CollectableCells6,
    b'maps/b_batt1.bsp': CollectableCells12,
    b'progs/armor.mdl': None,  # depends on skin, so has to be handled in special way
    b'progs/g_shot.mdl': CollectableSuperShotgun,
    b'progs/g_nail.mdl': CollectableNailgun,
    b'progs/g_nail2.mdl': CollectableSuperNailgun,
    b'progs/g_rock.mdl': CollectableGrenadeLauncher,
    b'progs/g_rock2.mdl': CollectableRocketLauncher,
    b'progs/g_light.mdl': CollectableLightningGun,
}

@dataclasses.dataclass
class SoundCollectEvent:
    sound_num: int
    origin: list[float]
    sound: CollectSound

@dataclasses.dataclass
class CollectEvent:
    block_index: int
    sound_event: SoundCollectEvent
    text: bytes

@dataclasses.dataclass
class Collectable:
    entity_num: int
    type: None
    collect_event: CollectEvent
    frame_consumed: int

    def will_collect(self, stats, is_coop):
        return self.type.will_collect(stats, is_coop)
    def will_disappear(self, stats, is_coop):
        return self.type.will_disappear(stats, is_coop)

    def get_pickup(self, stat_type):
        return sum(x.value for x in self.type.gives if isinstance(x, stat_type))
    def get_pickup_items(self):
        item_flags = 0
        for flags in [x.value for x in self.type.gives if isinstance(x, Item)]:
            item_flags |= flags
        return item_flags

    def bounds(self, origin):
        return collision.bounds_collectable(origin, self.type.mins, self.type.maxs)

@dataclasses.dataclass
class CollectablePersistant:
    collectable: Collectable
    origins: list[list[float]]

    def bounds(self, frame: int):
        return self.collectable.bounds(self.origins[frame])

@dataclasses.dataclass
class CollectableActiveFrame:
    collectable: Collectable
    origin: list[float]

    def bounds(self):
        return self.collectable.bounds(self.origin)


def get_precaches(demo):
    server_info_message = [m for b in demo.blocks for m in b.messages
                           if isinstance(m, messages.ServerInfoMessage)]
    assert len(server_info_message) == 1
    return (server_info_message[0].models_precache,
            server_info_message[0].sounds_precache)

def get_static_collectables(demo, models_precache):
    collectables_static = dict()
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.SpawnBaselineMessage):
                model_name = models_precache[m.modelindex]
                if model_name in COLLECTABLE_MODELS_MAP.keys():
                    assert m.entity_num not in collectables_static
                    if model_name == b'progs/armor.mdl':
                        if m.skin == 0:
                            collectable_type = CollectableGreenArmor
                        elif m.skin == 1:
                            collectable_type = CollectableYellowArmor
                        else:
                            assert m.skin == 2
                            collectable_type = CollectableRedArmor
                    else:
                        collectable_type = COLLECTABLE_MODELS_MAP[model_name]
                    collectables_static[m.entity_num] = CollectablePersistant(
                        Collectable(m.entity_num, collectable_type, None, math.inf),
                        [list(m.origin) for _ in range(len(demo.blocks))])
            elif isinstance(m, messages.EntityUpdateMessage):
                if m.num in collectables_static:
                    if m.flags & messages.UpdateFlags.ORIGIN1:
                        collectables_static[m.num].origins[i][0] = m.origin[0]
                    if m.flags & messages.UpdateFlags.ORIGIN2:
                        collectables_static[m.num].origins[i][1] = m.origin[1]
                    if m.flags & messages.UpdateFlags.ORIGIN3:
                        collectables_static[m.num].origins[i][2] = m.origin[2]
    return collectables_static

def get_static_collectables_by_frame(demo, models_precache):
    statics = get_static_collectables(demo, models_precache)
    collectables_by_frame = [[] for _ in range(len(demo.blocks))]
    for i, block in enumerate(demo.blocks):
        has_entity_update = False
        for m in block.messages:
            if isinstance(m, messages.SpawnBaselineMessage):
                # this is so that we can collect items instantly on unpause,
                # because there is not a single EntityUpdateMessage for those
                if m.entity_num in statics:
                    assert i == 1
                    collectables_by_frame[i].append(CollectableActiveFrame(
                        statics[m.entity_num].collectable,
                        statics[m.entity_num].origins[i]))
            elif isinstance(m, messages.EntityUpdateMessage):
                if m.num in statics:
                    has_entity_update = True
                    collectables_by_frame[i].append(CollectableActiveFrame(
                        statics[m.num].collectable, statics[m.num].origins[i]))
        if not any((isinstance(m, messages.TimeMessage) or
                    isinstance(m, messages.SpawnBaselineMessage))
                   for m in block.messages):
            assert not has_entity_update
            # this is so that intermediate frames that do not have a TimeMessage
            # still provide the info as if accessing the proper frame
            collectables_by_frame[i] = collectables_by_frame[i-1]
    return collectables_by_frame

def get_backpacks_by_frame(demo, models_precache):
    backpacks_by_frame = [[] for _ in range(len(demo.blocks))]
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.EntityUpdateMessage):
                if m.modelindex and models_precache[m.modelindex] == b'progs/backpack.mdl':
                    backpacks_by_frame[i].append(CollectableActiveFrame(
                        Collectable(m.num, CollectableBackpack, None, math.inf),
                        m.origin))
    return backpacks_by_frame

def get_viewent_num(demo):
    set_view_messages = [m for b in demo.blocks for m in b.messages
                         if isinstance(m, messages.SetViewMessage)]
    assert len(set_view_messages) >= 1
    viewent_num = set_view_messages[0].viewentity_id
    assert all([m.viewentity_id == viewent_num for m in set_view_messages])
    return viewent_num

def get_collection_sounds(block: format.Block, sounds_precache: list[str], viewent_num: int) -> typing.Iterator[SoundCollectEvent]:
    for m in block.messages:
        if isinstance(m, messages.SoundMessage):
            sound_name = sounds_precache[m.sound_num]
            if m.ent == viewent_num and sound_name in COLLECT_SOUNDS:
                yield SoundCollectEvent(
                    m.sound_num, m.pos, CollectSound(sound_name))

def get_collection_prints(block: format.Block) -> typing.Iterator[bytes]:
    ignore_items = [b"silver key", b"gold key", b"silver keycard",
                    b"gold keycard", b"silver runekey", b"gold runekey",
                    b"Quad Damage", b"Biosuit", b"Ring of Shadows",
                    b"Pentagram of Protection"]
    ignore_texts = [b"You got the " + x + b"\n" for x in ignore_items]
    text = b""
    for m in block.messages:
        if isinstance(m, messages.PrintMessage):
            if (m.text.startswith(b"You get") or
                m.text.startswith(b"You got") or
                m.text.startswith(b"You receive")):
                assert not text
                text += m.text
            elif text:
                text += m.text
        elif isinstance(m, messages.StuffTextMessage):
            if m.text == b"bf\n":
                if text and not any(x == text for x in ignore_texts):
                    yield text
                text = b""

def get_collection_events(demo: format.Demo, sounds_precache: list[str]) -> typing.Iterator[CollectEvent]:
    viewent_num = get_viewent_num(demo)
    for i, block in enumerate(demo.blocks[:-1]):
        sounds = get_collection_sounds(block, sounds_precache, viewent_num)
        prints = get_collection_prints(demo.blocks[i+1])
        for sound, print in zip(sounds, prints, strict=True):
            yield CollectEvent(i, sound, print)

def get_client_positions(demo, client_num):
    client_positions = []
    for block in demo.blocks:
        client_messages = [m for m in block.messages
                           if isinstance(m, messages.EntityUpdateMessage) and m.num == client_num]
        if client_messages:
            assert len(client_messages) == 1
            client_positions.append(client_messages[0].origin)
        else:
            client_positions.append([math.inf]*3)
    return client_positions

def is_sound_from_client_position(client_origin, sound_origin) -> bool:
    assert len(client_origin) == len(sound_origin) == 3
    # sounds are created at center of bounding box, see SV_StartSound
    client_center = collision.PlayerBounds.center(client_origin)
    max_diff = max(abs(x - y) for x, y in zip(client_center, sound_origin))
    # can't check for equality as this does not seem to be accurate all the time
    # for some reason... Perhaps the client origin can change slightly between
    # an entity update and when the sound is created.
    return max_diff < 1.5

def find_closest_collectable_frame_to_client(client_origin,
                                             collectable_active_frames):
    closest_distance = math.inf
    closest_collectable = None
    for collectable_frame in collectable_active_frames:
        distance = collision.distance(collision.bounds_player(client_origin),
                                      collectable_frame.bounds())
        if distance < closest_distance:
            closest_collectable = collectable_frame
            closest_distance = distance
    return closest_collectable, closest_distance

def get_backpack_contents(collection_text: bytes) -> typing.Iterator:
    pattern = (b'You get '
               b'(?:([1-9]\d*) shells)?(?:, )?'
               b'(?:([1-9]\d*) nails)?(?:, )?'
               b'(?:([1-9]\d*) rockets)?(?:, )?'
               b'(?:([1-9]\d*) cells)?\\n')
    match = re.match(pattern, collection_text)
    for i, stat_type in enumerate((Shells, Nails, Rockets, Cells)):
        if match.group(i+1):
            yield stat_type(int(match.group(i+1)))

def get_collections(demo):
    models_precache, sounds_precache = get_precaches(demo)
    viewent_num = get_viewent_num(demo)
    collection_events = get_collection_events(demo, sounds_precache)
    statics_by_frame = get_static_collectables_by_frame(demo, models_precache)
    backpacks_by_frame = get_backpacks_by_frame(demo, models_precache)
    client_positions = get_client_positions(demo, viewent_num)

    static_collections = [[] for _ in range(len(demo.blocks))]
    backpack_collections = [[] for _ in range(len(demo.blocks))]
    for event in collection_events:
        client_origin = client_positions[event.block_index]
        assert is_sound_from_client_position(client_origin=client_origin,
                                             sound_origin=event.sound_event.origin)

        statics_candidates = [static for static in statics_by_frame[event.block_index-1]
                              if static.collectable.type.collect_sound == event.sound_event.sound]
        closest_static, distance_static = find_closest_collectable_frame_to_client(
            client_origin, statics_candidates)

        closest_backpack = None
        distance_backpack = math.inf
        if event.sound_event.sound == CollectSound.AMMO:
            closest_backpack, distance_backpack = find_closest_collectable_frame_to_client(
                client_origin, backpacks_by_frame[event.block_index-1])

        if distance_static < distance_backpack:
            assert event.text == closest_static.collectable.type.print_text
            statics_by_frame[event.block_index-1].remove(closest_static)
            distance = distance_static
            closest = closest_static.collectable
            static_collections[event.block_index].append(closest)
        else:
            assert event.text.startswith(b'You get ')
            backpacks_by_frame[event.block_index-1].remove(closest_backpack)
            distance = distance_backpack
            closest = closest_backpack.collectable
            closest.type.gives = list(get_backpack_contents(event.text))
            backpack_collections[event.block_index].append(closest)
        assert distance < 0.5
        assert event.sound_event.sound == closest.type.collect_sound
        closest.sound_event = event.sound_event

    return static_collections, backpack_collections

def get_static_collections(demo):
    static_collections, _ = get_collections(demo)
    return static_collections

def get_backpack_collections(demo):
    _, backpack_collections = get_collections(demo)
    return backpack_collections

def get_first_active_block_index(demo):
    for i, block in enumerate(demo.blocks):
        for m in block.messages:
            if isinstance(m, messages.TimeMessage):
                if m.time > 1.22777784:
                    return i

def get_possible_collections(demo):
    models_precache, _ = get_precaches(demo)
    collectables = get_static_collectables(demo, models_precache)
    client_positions = get_client_positions(demo, get_viewent_num(demo))
    first_active_block_index = get_first_active_block_index(demo)
    original_collections = get_static_collections(demo)

    possible_pickups = [[] for _ in range(len(demo.blocks))]
    for i, pos in enumerate(client_positions):
        for collectable in collectables.values():
            tolerance = 0.0
            if i < first_active_block_index:
                # do not expect any collection before first active block index
                tolerance = -math.inf
            elif i == first_active_block_index:
                # It seems like client position is not 100% reliable on the
                # first frame. Instant pickups may therefore not be recognized
                # with a tolerance of 0. Therefore we allow a bit more leeway on
                # the first frame
                tolerance = 0.5
            distance = collision.distance(collision.bounds_player(pos),
                                          collectable.bounds(frame=i-1))

            orig_collection = [c for c in original_collections[i]
                if c.entity_num == collectable.collectable.entity_num]
            assert len(orig_collection) <= 1
            is_collected_in_original = len(orig_collection) > 0
            if is_collected_in_original:
                orig_collection = orig_collection[0]
                assert distance <= tolerance
                center = collision.PlayerBounds.center(pos)
                assert abs(orig_collection.sound_event.origin[0] - center[0]) <= tolerance
                assert abs(orig_collection.sound_event.origin[1] - center[1]) <= tolerance
                # z-coordinate does not always seem accurate for some reason
                assert abs(orig_collection.sound_event.origin[2] - center[2]) < 1.0

            # Usually, collections only seem to happen when bounding boxes are
            # strictly overlapping (i.e. distance < 0.0). In some exceptions,
            # touching (i.e. distance == 0.0) can be enough though. To include
            # those special cases, we also add it, if it was picked up in the
            # original (and we assert distance == 0.0 above for that case).
            if distance < tolerance or is_collected_in_original:
                possible_pickups[i].append(collectable.collectable)
    return possible_pickups

def get_damage(demo):
    damage = []
    for block in demo.blocks:
        damage_messages = [m for m in block.messages
                           if isinstance(m, messages.DamageMessage)]
        assert len(damage_messages) == 1 or len(damage_messages) == 0
        if len(damage_messages) == 0:
            damage.append(messages.DamageMessage(0, 0, []))
        else:
            damage.append(damage_messages[0])
    return damage


def verify_damage_message(damage: messages.DamageMessage, armor: int, reduction: float):
    damage_ceiled = damage.blood + damage.armor
    assert damage_ceiled == math.ceil(damage_ceiled)
    # this can break down if there are several separate damage sources being
    # applied on the same frame, and the sum of the rounded up values is
    # larger than rounding up the summed value
    if reduction == 0.0:
        assert damage.blood == damage_ceiled
    else:
        armor_lower_bound, armor_upper_bound = lost_armor_bounds(
            damage_ceiled, armor, reduction)
        assert armor_lower_bound <= damage.armor
        assert damage.armor <= armor_upper_bound
        blood_lower_bound = damage_ceiled - armor_upper_bound
        blood_upper_bound = damage_ceiled - armor_lower_bound
        assert blood_lower_bound <= damage.blood
        assert damage.blood <= blood_upper_bound

def get_ammo_for_activeweapon(stats: format.ClientStats):
    if stats.activeweapon == 0:  # axe
        return 0, 0
    elif stats.activeweapon == ItemFlags.SHOTGUN:
        return ItemFlags.SHELLS, stats.shells
    elif stats.activeweapon == ItemFlags.SUPER_SHOTGUN:
        return ItemFlags.SHELLS, stats.shells
    elif stats.activeweapon == ItemFlags.NAILGUN:
        return ItemFlags.NAILS, stats.nails
    elif stats.activeweapon == ItemFlags.SUPER_NAILGUN:
        return ItemFlags.NAILS, stats.nails
    elif stats.activeweapon == ItemFlags.GRENADE_LAUNCHER:
        return ItemFlags.ROCKETS, stats.rockets
    elif stats.activeweapon == ItemFlags.ROCKET_LAUNCHER:
        return ItemFlags.ROCKETS, stats.rockets
    elif stats.activeweapon == ItemFlags.LIGHTNING:
        return ItemFlags.CELLS, stats.cells
    else:
        raise ValueError("Unknown activeweapon")

def rebuild_stats(new_start: format.ClientStats,
                  old_stats_list: list[format.ClientStats],
                  backpack_collections, old_static_collections,
                  possible_collections, damage, is_coop):
    assert len(old_stats_list) == len(damage)

    old_stats_previous = None
    stats = ClientStatsAccessor(copy.deepcopy(new_start))
    stats_list = []
    actual_collections = [[] for _ in range(len(possible_collections))]

    for i, old_stats_data in enumerate(old_stats_list):
        if not old_stats_data:
            stats_list.append(None)
            continue
        old_stats = ClientStatsAccessor(old_stats_data)
        if not old_stats_previous:
            old_stats_previous = old_stats

        old_lost_armor = damage[i].armor
        if all(c.get_pickup(Armor) == 0.0 for c in old_static_collections[i]):
            assert (old_stats_previous.armor - old_stats.armor) == old_lost_armor

        old_reduction = get_damage_reduction(old_stats_previous.items)
        verify_damage_message(damage[i], old_stats_previous.armor, old_reduction)
        old_damage_ceiled = damage[i].blood + damage[i].armor

        old_collected_health = sum(c.get_pickup(Health)
                                   for c in old_static_collections[i])
        old_stats_health_before_loss = Health.bound(
            old_stats_previous.health + old_collected_health, old_stats.items)
        old_lost_health = (old_stats_health_before_loss - old_stats.health)
        assert old_lost_health >= 0.0

        new_reduction = get_damage_reduction(stats.items)
        if (old_damage_ceiled == 0.0 or (old_reduction == new_reduction and (old_lost_armor == 0.0 or (old_lost_armor != old_stats_previous.armor and old_lost_armor <= stats.armor)))):
            stats.armor -= old_lost_armor
            stats.health -= old_lost_health
        else:
            # TODO: gotta replace the damage message... :(
            lost_armor_lower_bound, lost_armor_upper_bound = lost_armor_bounds(
                old_damage_ceiled, stats.armor, new_reduction)
            if lost_armor_lower_bound != lost_armor_upper_bound:
                print("Warning: Health/Armor reconstruction might be inaccurate")
            lost_armor = lost_armor_upper_bound
            stats.armor -= lost_armor
            # we can only handle either fully ignored damage, or fully applied
            # damage, not something in between
            assert old_lost_health == 0.0 or old_lost_health == damage[i].blood
            if old_lost_health != 0.0:
                lost_health = old_damage_ceiled - lost_armor
                stats.health -= lost_health

        if stats.armor == 0:
            stats.items &= ~(ItemFlags.ARMOR1|ItemFlags.ARMOR2|ItemFlags.ARMOR3)
        #assert stats.health >= MIN_HEALTH
        assert stats.armor >= 0

        for stat_type in (Shells, Nails, Rockets, Cells):
            collected = sum(c.get_pickup(stat_type) for c in
                            (old_static_collections[i] + backpack_collections[i]))
            old_value_before_loss = stat_type.bound(
                old_stats_previous[stat_type] + collected, old_stats.items)
            lost = old_value_before_loss - old_stats[stat_type]
            assert lost >= 0
            stats[stat_type] -= lost
            assert stats[stat_type] >= stat_type.min

        for collectable in possible_collections[i]:
            if collectable.will_collect(stats, is_coop) and collectable.frame_consumed > i:
                picked_up_in_original = any(c.entity_num == collectable.entity_num for c in old_static_collections[i])
                if collectable.will_collect(old_stats_previous, is_coop) and not picked_up_in_original:
                    # for some reason this collectable wasnt picked up in original demo
                    # despite stats indicating that it will be picked up. perhaps
                    # another coop player already got that collectable or something weird
                    # is going on like with the nailgun in the trap on e1m3
                    continue

                actual_collections[i].append(collectable)
                if collectable.will_disappear(stats, is_coop):
                    collectable.frame_consumed = i

                stats.items |= collectable.get_pickup_items()
                for stat_type in (Health, Shells, Nails, Rockets, Cells):
                    collected_value = collectable.get_pickup(stat_type)
                    stats[stat_type] = stat_type.bound(
                        stats[stat_type] + collected_value, stats.items)
                collected_armor = collectable.get_pickup(Armor)
                if collected_armor > 0:
                    stats.armor = collected_armor

        for stat_type in (Shells, Nails, Rockets, Cells):
            backpack_value = sum(c.get_pickup(stat_type)
                                 for c in backpack_collections[i])
            stats[stat_type] = stat_type.bound(
                stats[stat_type] + backpack_value, stats.items)

        added_items = (old_stats.items & ~old_stats_previous.items)
        removed_items = (~old_stats.items & old_stats_previous.items)
        stats.items |= added_items
        stats.items &= ~removed_items

        stats.activeweapon = old_stats.activeweapon  # TODO: set to new_start first. then set to something else if 0 ammo is reached. Also fix which ammo is shown in hud with that
        ammo_item_flag, stats.ammo = get_ammo_for_activeweapon(stats)
        if ammo_item_flag != 0 and stats.ammo <= 0:
            # TODO: switch in the next x frames
            print("Warning: This weapon cannot be active")
        stats.items &= ~(ItemFlags.SHELLS|ItemFlags.NAILS|ItemFlags.ROCKETS|ItemFlags.CELLS)
        stats.items |= ammo_item_flag

        stats_list.append(copy.deepcopy(stats))
        old_stats_previous = old_stats
    return stats_list, actual_collections


def fix_collection_events(actual_collections, demo):
    models_precache, sounds_precache = get_precaches(demo)
    changeable_collections = get_static_collections(demo)
    viewent_num = get_viewent_num(demo)
    client_positions = get_client_positions(demo, viewent_num)

    static_collectables = get_static_collectables(demo, models_precache)

    times = demo.get_time()
    blocks_to_remove = []
    for i, block in enumerate(demo.blocks):
        equal = []
        for x in changeable_collections[i]:
            for y in actual_collections[i]:
                if x.entity_num == y.entity_num:
                    equal.append(x.entity_num)
        collections_to_remove = [c for c in changeable_collections[i] if c.entity_num not in equal]
        collections_to_add = [c for c in actual_collections[i] if c.entity_num not in equal]

        for c in collections_to_remove:
            print(f"removed collection: {c.type} at time {times[i]}")

            sounds_to_remove = [m for m in block.messages
                                if (isinstance(m, messages.SoundMessage) and
                                    m.sound_num == c.sound_event.sound_num)]
            assert len(sounds_to_remove) == 1
            block.messages.remove(sounds_to_remove[0])

            # TODO: assert that this really is the info block for this pickup with
            # pickup message, screenflash and so on
            blocks_to_remove.append(i + 1)

            # TODO: can we somehow figure out if the collectable is in view to not spam
            # these messages in every block?
            flags = messages.UpdateFlags.SIGNAL
            if c.entity_num > 255:
                flags |= messages.UpdateFlags.MOREBITS|messages.UpdateFlags.LONGENTITY
            last_origin = None
            if (static_collectables[c.entity_num].origins[i-1] !=
                static_collectables[c.entity_num].origins[0]):
                last_origin = static_collectables[c.entity_num].origins[i-1]
                flags |= (messages.UpdateFlags.ORIGIN1|
                          messages.UpdateFlags.ORIGIN2|
                          messages.UpdateFlags.ORIGIN3)
            message = messages.EntityUpdateMessage(
                flags, c.entity_num, None, None, None, None, None, last_origin,
                None, None, None, None, None, None, None)
            for j in range(i, len(demo.blocks)):
                if any([isinstance(m, messages.TimeMessage) for m in demo.blocks[j].messages]):
                    demo.blocks[j].messages.append(message)

        for c in collections_to_add:
            print(f"added collection: {c.type} at time {times[i]}")

            sound_name = c.type.collect_sound.value
            sound_num = sounds_precache.index(sound_name)
            block.messages.append(messages.SoundMessage(flags=0, volume=255,
                attenuation=1.0, ent=viewent_num, channel=3, sound_num=sound_num,
                pos=collision.PlayerBounds.center(client_positions[i])))
            block.messages.append(messages.PrintMessage(text=c.type.print_text))
            block.messages.append(messages.StuffTextMessage(text=b'bf\n'))
            for j in range(i, len(demo.blocks)):
                for m in [m for m in demo.blocks[j].messages if isinstance(m, messages.EntityUpdateMessage) and m.num == c.entity_num]:
                    demo.blocks[j].messages.remove(m)

    for i in reversed(blocks_to_remove):
        del demo.blocks[i]
