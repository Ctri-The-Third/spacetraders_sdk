#
# deposits
#

COMMON_METALS = [
    "ALUMINUM_ORE",
    "IRON_ORE",
    "COPPER_ORE",
]
MINERAL_DEPOSITS = ["SILICON_CRYSTALS", "QUARTZ_SAND"]
PRECIOUS_METAL_DEPOSITS = ["SILVER_ORE", "GOLD_ORE", "PLATINUM_ORE"]
RARE_METAL_DEPOSITS = ["MERITIUM_ORE", "URANITE_ORE"]
ICE_CRYSTAL_DEPOSITS = [
    "ICE_WATER",
    "AMMONIA_ICE",
    "LIQUID_HYDROGEN",
    "LIQUID_NITROGEN",
]
EXTRACTABLES = [
    "QUARTZ_SAND",
    "SILICON_CRYSTALS",
    "PRECIOUS_STONES",
    "ICE_WATER",
    "AMMONIA_ICE",
    "IRON_ORE",
    "COPPER_ORE",
    "SILVER_ORE",
    "ALUMINUM_ORE",
    "GOLD_ORE",
    "PLATINUM_ORE",
    "DIAMONDS",
    "URANITE_ORE",
    "MERITIUM_ORE",
]
SHIPONABLES = [
    "HYDROCARBON",
    "LIQUID_HYDROGEN",
    "LIQUID_NITROGEN",
]
#
# mounts
#
SURVEYOR_SYMBOLS = ["MOUNT_SURVEYOR_I", "MOUNT_SURVEYOR_II", "MOUNT_SURVEYOR_III"]
MINING_SYMBOLS = [
    "MOUNT_MINING_LASER_I",
    "MOUNT_MINING_LASER_II",
    "MOUNT_MINING_LASER_III",
]
#
# errors
#
SIPHON_SYMBOLS = ["MOUNT_GAS_SIPHON_I", "MOUNT_GAS_SIPHON_II", "MOUNT_GAS_SIPHON_III"]
ERRROR_COOLDOWN = 4000

ORBITAL_TYPES = ["ORBITAL_STATION", "MOON"]
PARENT_TYPES = ["PLANET", "GAS_GIANT"]

SUPPLY_LEVELS = {
    "SCARCE": 1,
    "LIMITED": 2,
    "MODERATE": 3,
    "HIGH": 4,
    "ABUNDANT": 5,
}

ACTIVITY_LEVELS = {
    "RESTRICTED": 0.5,
    "WEAK": 1,
    "GROWING": 2,
    "STRONG": 3,
}

ORE_MANUFACRED_BY = {
    "IRON_ORE": ["EXPLOSIVES"],
    "ALUMINUM_ORE": ["EXPLOSIVES"],
    "COPPER_ORE": ["EXPLOSIVES"],
}
MANUFACTURED_BY = {
    "CULTURAL_ARTIFACTS": ["LAB_INSTRUMENTS"],
    "PLASTICS": ["LIQUID_HYDROGEN"],
    "FERTILIZERS": ["LIQUID_NITROGEN"],
    "FUEL": ["HYDROCARBON"],
    "IRON": ["IRON_ORE"],
    "ALUMINUM": ["ALUMINUM_ORE"],
    "POLYNUCLEOTIDES": ["LIQUID_HYDROGEN", "LIQUID_NITROGEN"],
    "EXPLOSIVES": ["LIQUID_HYDROGEN", "LIQUID_NITROGEN"],
    "COPPER": ["COPPER_ORE"],
    "SILVER": ["SILVER_ORE"],
    "PLATINUM": ["PLATINUM_ORE"],
    "GOLD": ["GOLD_ORE"],
    "URANITE": ["URANITE_ORE"],
    "MERITIUM": ["MERITIUM_ORE"],
    "AMMUNITION": ["IRON", "LIQUID_NITROGEN"],
    "FAB_MATS": ["IRON", "QUARTZ_SAND"],
    "FOOD": ["FERTILIZERS"],
    "FABRICS": ["FERTILIZERS"],
    "ELECTRONICS": ["SILICON_CRYSTALS", "COPPER"],
    "MACHINERY": ["IRON"],
    "EQUIPMENT": ["ALUMINUM", "PLASTICS"],
    "JEWELRY": ["GOLD", "SILVER", "PRECIOUS_STONES", "DIAMONDS"],
    "MICROPROCESSORS": ["SILICON_CRYSTALS", "COPPER"],
    "FIREARMS": ["IRON", "AMMUNITION"],
    "ASSAULT_RIFLES": ["ALUMINUM", "AMMUNITION"],
    "CLOTHING": ["FABRICS"],
    "SHIP_PLATING": ["ALUMINUM", "MACHINERY"],
    "SHIP_PARTS": ["EQUIPMENT", "ELECTRONICS"],
    "MEDICINE": ["FABRICS", "POLYNUCLEOTIDES"],
    "DRUGS": ["AMMONIA_ICE", "POLYNUCLEOTIDES"],
    "MILITARY_EQUIPMENT": ["ALUMINUM", "ELECTRONICS"],
    "LAB_INSTRUMENTS": ["ELECTRONICS", "EQUIPMENT"],
    "BIOCOMPOSITES": ["FABRICS", "POLYNUCLEOTIDES"],
    "ADVANCED_CIRCUITRY": ["ELECTRONICS", "MICROPROCESSORS"],
    "REACTOR_SOLAR_I": ["IRON", "MACHINERY"],
    "REACTOR_FUSION_I": ["IRON", "MACHINERY"],
    "REACTOR_FISSION_I": ["IRON", "MACHINERY"],
    "REACTOR_CHEMICAL_I": ["IRON", "MACHINERY"],
    "REACTOR_ANTIMATTER_I": ["IRON", "MACHINERY"],
    "ENGINE_IMPULSE_DRIVE_I": ["IRON", "MACHINERY"],
    "ENGINE_ION_DRIVE_I": ["IRON", "MACHINERY"],
    "MODULE_CARGO_HOLD_I": ["IRON", "MACHINERY"],
    "MODULE_CARGO_HOLD_II": ["ALUMINUM", "MACHINERY"],
    "MODULE_MINERAL_PROCESSOR_I": ["IRON", "MACHINERY"],
    "MODULE_GAS_PROCESSOR_I": ["IRON", "MACHINERY"],
    "MODULE_CREW_QUARTERS_I": ["IRON", "MACHINERY", "FABRICS"],
    "MODULE_ENVOY_QUARTERS_I": ["IRON", "MACHINERY", "FABRICS"],
    "MODULE_PASSENGER_CABIN_I": ["IRON", "MACHINERY", "FABRICS"],
    "MODULE_SCIENCE_LAB_I": ["PLATINUM", "MACHINERY", "ADVANCED_CIRCUITRY"],
    "MODULE_ORE_REFINERY_I": ["PLATINUM", "MACHINERY"],
    "MODULE_FUEL_REFINERY_I": ["PLATINUM", "MACHINERY"],
    "MODULE_MICRO_REFINERY_I": ["PLATINUM", "MACHINERY"],
    "MOUNT_GAS_SIPHON_I": ["IRON", "MACHINERY"],
    "MOUNT_GAS_SIPHON_II": ["ALUMINUM", "MACHINERY"],
    "MOUNT_SURVEYOR_I": ["IRON", "MACHINERY", "ELECTRONICS"],
    "MOUNT_SURVEYOR_II": ["ALUMINUM", "MACHINERY", "ELECTRONICS"],
    "MOUNT_SENSOR_ARRAY_I": ["IRON", "MACHINERY", "ELECTRONICS"],
    "MOUNT_SENSOR_ARRAY_II": ["ALUMINUM", "MACHINERY", "ELECTRONICS"],
    "MOUNT_MINING_LASER_I": ["IRON", "MACHINERY", "DIAMONDS"],
    "MOUNT_MINING_LASER_II": ["ALUMINUM", "MACHINERY", "DIAMONDS"],
    "MOUNT_TURRET_I": ["IRON", "MACHINERY"],
    "MOUNT_LASER_CANNON_I": ["IRON", "MACHINERY", "DIAMONDS"],
    "MOUNT_MISSILE_LAUNCHER_I": ["IRON", "MACHINERY"],
    "QUANTUM_STABILIZERS": ["PLATINUM", "ADVANCED_CIRCUITRY", "URANITE"],
    "ANTIMATTER": ["LAB_INSTRUMENTS", "ADVANCED_CIRCUITRY"],
    "EXOTIC_MATTER": ["LAB_INSTRUMENTS", "ADVANCED_CIRCUITRY"],
    "RELIC_TECH": ["LAB_INSTRUMENTS", "EQUIPMENT"],
    "NOVEL_LIFEFORMS": ["LAB_INSTRUMENTS", "EQUIPMENT"],
    "BOTANICAL_SPECIMENS": ["LAB_INSTRUMENTS", "EQUIPMENT"],
    "AI_MAINFRAMES": ["ADVANCED_CIRCUITRY", "MICROPROCESSORS"],
    "QUANTUM_DRIVES": ["ADVANCED_CIRCUITRY", "URANITE"],
    "GRAVITON_EMITTERS": ["ADVANCED_CIRCUITRY", "MERITIUM"],
    "ROBOTIC_DRONES": ["ADVANCED_CIRCUITRY", "ALUMINUM"],
    "CYBER_IMPLANTS": ["ADVANCED_CIRCUITRY", "BIOCOMPOSITES"],
    "NANOBOTS": ["POLYNUCLEOTIDES", "LAB_INSTRUMENTS"],
    "GENE_THERAPEUTICS": ["POLYNUCLEOTIDES", "LAB_INSTRUMENTS"],
    "NEURAL_CHIPS": ["POLYNUCLEOTIDES", "ADVANCED_CIRCUITRY"],
    "MOOD_REGULATORS": ["POLYNUCLEOTIDES", "LAB_INSTRUMENTS"],
    "VIRAL_AGENTS": ["POLYNUCLEOTIDES", "LAB_INSTRUMENTS"],
    "MICRO_FUSION_GENERATORS": ["ADVANCED_CIRCUITRY", "PLATINUM", "DIAMONDS"],
    "SUPERGRAINS": ["FERTILIZERS", "POLYNUCLEOTIDES", "LAB_INSTRUMENTS"],
    "LASER_RIFLES": ["DIAMONDS", "PLATINUM", "ADVANCED_CIRCUITRY"],
    "HOLOGRAPHICS": ["GOLD", "SILVER", "ADVANCED_CIRCUITRY"],
    "ENGINE_ION_DRIVE_II": ["PLATINUM", "ADVANCED_CIRCUITRY"],
    "ENGINE_HYPER_DRIVE_I": ["PLATINUM", "ADVANCED_CIRCUITRY"],
    "MODULE_CARGO_HOLD_III": ["PLATINUM", "MACHINERY", "ADVANCED_CIRCUITRY"],
    "MODULE_JUMP_DRIVE_I": ["IRON", "ADVANCED_CIRCUITRY"],
    "MODULE_JUMP_DRIVE_II": ["PLATINUM", "ADVANCED_CIRCUITRY", "GOLD"],
    "MODULE_JUMP_DRIVE_III": ["PLATINUM", "ADVANCED_CIRCUITRY", "GOLD", "MERITIUM"],
    "MODULE_WARP_DRIVE_I": ["IRON", "ADVANCED_CIRCUITRY"],
    "MODULE_WARP_DRIVE_II": ["PLATINUM", "ADVANCED_CIRCUITRY", "URANITE"],
    "MODULE_WARP_DRIVE_III": ["PLATINUM", "ADVANCED_CIRCUITRY", "MERITIUM"],
    "MOUNT_GAS_SIPHON_III": ["PLATINUM", "MACHINERY", "ADVANCED_CIRCUITRY"],
    "MODULE_SHIELD_GENERATOR_I": ["IRON", "MACHINERY", "URANITE"],
    "MODULE_SHIELD_GENERATOR_II": ["ALUMINUM", "MACHINERY", "URANITE"],
    "MOUNT_SURVEYOR_III": ["PLATINUM", "MACHINERY", "ADVANCED_CIRCUITRY"],
    "MOUNT_SENSOR_ARRAY_III": [
        "PLATINUM",
        "MACHINERY",
        "ADVANCED_CIRCUITRY",
        "URANITE",
    ],
    "MOUNT_MINING_LASER_III": [
        "PLATINUM",
        "MACHINERY",
        "ADVANCED_CIRCUITRY",
        "URANITE",
    ],
    "SHIP_PROBE": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_MINING_DRONE": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_SIPHON_DRONE": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_LIGHT_HAULER": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_COMMAND_FRIGATE": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_INTERCEPTOR": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_EXPLORER": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_LIGHT_SHUTTLE": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_HEAVY_FREIGHTER": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_ORE_HOUND": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_REFINING_FREIGHTER": ["SHIP_PLATING", "SHIP_PARTS"],
    "SHIP_SURVEYOR": ["SHIP_PLATING", "SHIP_PARTS"],
}
MANUFACTURES = {
    "LAB_INSTRUMENTS": [
        "CULTURAL_ARTIFACTS",
        "ANTIMATTER",
        "EXOTIC_MATTER",
        "RELIC_TECH",
        "NOVEL_LIFEFORMS",
        "BOTANICAL_SPECIMENS",
        "NANOBOTS",
        "GENE_THERAPEUTICS",
        "MOOD_REGULATORS",
        "VIRAL_AGENTS",
        "SUPERGRAINS",
    ],
    "LIQUID_HYDROGEN": ["PLASTICS", "POLYNUCLEOTIDES", "EXPLOSIVES"],
    "LIQUID_NITROGEN": ["FERTILIZERS", "POLYNUCLEOTIDES", "EXPLOSIVES", "AMMUNITION"],
    "HYDROCARBON": ["FUEL"],
    "IRON_ORE": ["IRON"],
    "ALUMINUM_ORE": ["ALUMINUM"],
    "COPPER_ORE": ["COPPER"],
    "SILVER_ORE": ["SILVER"],
    "PLATINUM_ORE": ["PLATINUM"],
    "GOLD_ORE": ["GOLD"],
    "URANITE_ORE": ["URANITE"],
    "MERITIUM_ORE": ["MERITIUM"],
    "IRON": [
        "AMMUNITION",
        "FAB_MATS",
        "MACHINERY",
        "FIREARMS",
        "REACTOR_SOLAR_I",
        "REACTOR_FUSION_I",
        "REACTOR_FISSION_I",
        "REACTOR_CHEMICAL_I",
        "REACTOR_ANTIMATTER_I",
        "ENGINE_IMPULSE_DRIVE_I",
        "ENGINE_ION_DRIVE_I",
        "MODULE_CARGO_HOLD_I",
        "MODULE_MINERAL_PROCESSOR_I",
        "MODULE_GAS_PROCESSOR_I",
        "MODULE_CREW_QUARTERS_I",
        "MODULE_ENVOY_QUARTERS_I",
        "MODULE_PASSENGER_CABIN_I",
        "MOUNT_GAS_SIPHON_I",
        "MOUNT_SURVEYOR_I",
        "MOUNT_SENSOR_ARRAY_I",
        "MOUNT_MINING_LASER_I",
        "MOUNT_TURRET_I",
        "MOUNT_LASER_CANNON_I",
        "MOUNT_MISSILE_LAUNCHER_I",
        "MODULE_JUMP_DRIVE_I",
        "MODULE_WARP_DRIVE_I",
        "MODULE_SHIELD_GENERATOR_I",
    ],
    "QUARTZ_SAND": ["FAB_MATS"],
    "FERTILIZERS": ["FOOD", "FABRICS", "SUPERGRAINS"],
    "SILICON_CRYSTALS": ["ELECTRONICS", "MICROPROCESSORS"],
    "COPPER": ["ELECTRONICS", "MICROPROCESSORS"],
    "ALUMINUM": [
        "EQUIPMENT",
        "ASSAULT_RIFLES",
        "SHIP_PLATING",
        "MILITARY_EQUIPMENT",
        "MODULE_CARGO_HOLD_II",
        "MOUNT_GAS_SIPHON_II",
        "MOUNT_SURVEYOR_II",
        "MOUNT_SENSOR_ARRAY_II",
        "MOUNT_MINING_LASER_II",
        "ROBOTIC_DRONES",
        "MODULE_SHIELD_GENERATOR_II",
    ],
    "PLASTICS": ["EQUIPMENT"],
    "GOLD": [
        "JEWELRY",
        "HOLOGRAPHICS",
        "MODULE_JUMP_DRIVE_II",
        "MODULE_JUMP_DRIVE_III",
    ],
    "SILVER": ["JEWELRY", "HOLOGRAPHICS"],
    "PRECIOUS_STONES": ["JEWELRY"],
    "DIAMONDS": [
        "JEWELRY",
        "MOUNT_MINING_LASER_I",
        "MOUNT_MINING_LASER_II",
        "MOUNT_LASER_CANNON_I",
        "MICRO_FUSION_GENERATORS",
        "LASER_RIFLES",
    ],
    "AMMUNITION": ["FIREARMS", "ASSAULT_RIFLES"],
    "FABRICS": [
        "CLOTHING",
        "MEDICINE",
        "BIOCOMPOSITES",
        "MODULE_CREW_QUARTERS_I",
        "MODULE_ENVOY_QUARTERS_I",
        "MODULE_PASSENGER_CABIN_I",
    ],
    "MACHINERY": [
        "SHIP_PLATING",
        "REACTOR_SOLAR_I",
        "REACTOR_FUSION_I",
        "REACTOR_FISSION_I",
        "REACTOR_CHEMICAL_I",
        "REACTOR_ANTIMATTER_I",
        "ENGINE_IMPULSE_DRIVE_I",
        "ENGINE_ION_DRIVE_I",
        "MODULE_CARGO_HOLD_I",
        "MODULE_CARGO_HOLD_II",
        "MODULE_MINERAL_PROCESSOR_I",
        "MODULE_GAS_PROCESSOR_I",
        "MODULE_CREW_QUARTERS_I",
        "MODULE_ENVOY_QUARTERS_I",
        "MODULE_PASSENGER_CABIN_I",
        "MODULE_SCIENCE_LAB_I",
        "MODULE_ORE_REFINERY_I",
        "MODULE_FUEL_REFINERY_I",
        "MODULE_MICRO_REFINERY_I",
        "MOUNT_GAS_SIPHON_I",
        "MOUNT_GAS_SIPHON_II",
        "MOUNT_SURVEYOR_I",
        "MOUNT_SURVEYOR_II",
        "MOUNT_SENSOR_ARRAY_I",
        "MOUNT_SENSOR_ARRAY_II",
        "MOUNT_MINING_LASER_I",
        "MOUNT_MINING_LASER_II",
        "MOUNT_TURRET_I",
        "MOUNT_LASER_CANNON_I",
        "MOUNT_MISSILE_LAUNCHER_I",
        "MODULE_CARGO_HOLD_III",
        "MOUNT_GAS_SIPHON_III",
        "MODULE_SHIELD_GENERATOR_I",
        "MODULE_SHIELD_GENERATOR_II",
        "MOUNT_SURVEYOR_III",
        "MOUNT_SENSOR_ARRAY_III",
        "MOUNT_MINING_LASER_III",
    ],
    "EQUIPMENT": [
        "SHIP_PARTS",
        "LAB_INSTRUMENTS",
        "RELIC_TECH",
        "NOVEL_LIFEFORMS",
        "BOTANICAL_SPECIMENS",
    ],
    "ELECTRONICS": [
        "SHIP_PARTS",
        "MILITARY_EQUIPMENT",
        "LAB_INSTRUMENTS",
        "ADVANCED_CIRCUITRY",
        "MOUNT_SURVEYOR_I",
        "MOUNT_SURVEYOR_II",
        "MOUNT_SENSOR_ARRAY_I",
        "MOUNT_SENSOR_ARRAY_II",
    ],
    "POLYNUCLEOTIDES": [
        "MEDICINE",
        "DRUGS",
        "BIOCOMPOSITES",
        "NANOBOTS",
        "GENE_THERAPEUTICS",
        "NEURAL_CHIPS",
        "MOOD_REGULATORS",
        "VIRAL_AGENTS",
        "SUPERGRAINS",
    ],
    "AMMONIA_ICE": ["DRUGS"],
    "MICROPROCESSORS": ["ADVANCED_CIRCUITRY", "AI_MAINFRAMES"],
    "PLATINUM": [
        "MODULE_SCIENCE_LAB_I",
        "MODULE_ORE_REFINERY_I",
        "MODULE_FUEL_REFINERY_I",
        "MODULE_MICRO_REFINERY_I",
        "QUANTUM_STABILIZERS",
        "MICRO_FUSION_GENERATORS",
        "LASER_RIFLES",
        "ENGINE_ION_DRIVE_II",
        "ENGINE_HYPER_DRIVE_I",
        "MODULE_CARGO_HOLD_III",
        "MODULE_JUMP_DRIVE_II",
        "MODULE_JUMP_DRIVE_III",
        "MODULE_WARP_DRIVE_II",
        "MODULE_WARP_DRIVE_III",
        "MOUNT_GAS_SIPHON_III",
        "MOUNT_SURVEYOR_III",
        "MOUNT_SENSOR_ARRAY_III",
        "MOUNT_MINING_LASER_III",
    ],
    "ADVANCED_CIRCUITRY": [
        "MODULE_SCIENCE_LAB_I",
        "QUANTUM_STABILIZERS",
        "ANTIMATTER",
        "EXOTIC_MATTER",
        "AI_MAINFRAMES",
        "QUANTUM_DRIVES",
        "GRAVITON_EMITTERS",
        "ROBOTIC_DRONES",
        "CYBER_IMPLANTS",
        "NEURAL_CHIPS",
        "MICRO_FUSION_GENERATORS",
        "LASER_RIFLES",
        "HOLOGRAPHICS",
        "ENGINE_ION_DRIVE_II",
        "ENGINE_HYPER_DRIVE_I",
        "MODULE_CARGO_HOLD_III",
        "MODULE_JUMP_DRIVE_I",
        "MODULE_JUMP_DRIVE_II",
        "MODULE_JUMP_DRIVE_III",
        "MODULE_WARP_DRIVE_I",
        "MODULE_WARP_DRIVE_II",
        "MODULE_WARP_DRIVE_III",
        "MOUNT_GAS_SIPHON_III",
        "MOUNT_SURVEYOR_III",
        "MOUNT_SENSOR_ARRAY_III",
        "MOUNT_MINING_LASER_III",
    ],
    "URANITE": [
        "QUANTUM_STABILIZERS",
        "QUANTUM_DRIVES",
        "MODULE_WARP_DRIVE_II",
        "MODULE_SHIELD_GENERATOR_I",
        "MODULE_SHIELD_GENERATOR_II",
        "MOUNT_SENSOR_ARRAY_III",
        "MOUNT_MINING_LASER_III",
    ],
    "MERITIUM": ["GRAVITON_EMITTERS", "MODULE_JUMP_DRIVE_III", "MODULE_WARP_DRIVE_III"],
    "BIOCOMPOSITES": ["CYBER_IMPLANTS"],
    "SHIP_PLATING": [
        "SHIP_PROBE",
        "SHIP_MINING_DRONE",
        "SHIP_SIPHON_DRONE",
        "SHIP_LIGHT_HAULER",
        "SHIP_COMMAND_FRIGATE",
        "SHIP_INTERCEPTOR",
        "SHIP_EXPLORER",
        "SHIP_LIGHT_SHUTTLE",
        "SHIP_HEAVY_FREIGHTER",
        "SHIP_ORE_HOUND",
        "SHIP_REFINING_FREIGHTER",
        "SHIP_SURVEYOR",
    ],
    "SHIP_PARTS": [
        "SHIP_PROBE",
        "SHIP_MINING_DRONE",
        "SHIP_SIPHON_DRONE",
        "SHIP_LIGHT_HAULER",
        "SHIP_COMMAND_FRIGATE",
        "SHIP_INTERCEPTOR",
        "SHIP_EXPLORER",
        "SHIP_LIGHT_SHUTTLE",
        "SHIP_HEAVY_FREIGHTER",
        "SHIP_ORE_HOUND",
        "SHIP_REFINING_FREIGHTER",
        "SHIP_SURVEYOR",
    ],
}
