from printer import *

test_lines = """
[CHAT WINDOW TEXT] [Wed Jul 13 00:35:34] TEST CHAR : Initiative Roll : 20 : (9 + 11 = 20)
[CHAT WINDOW TEXT] [Fri Jul  8 23:08:12] 10 AC - Undead - Chaotic Evil : Fortitude Save : *failure* : (9 + 1 = 10 vs. DC: 38)
[CHAT WINDOW TEXT] [Fri Jul  8 23:16:38] TEST CHAR : Reflex Save vs. Electricity : *success* : (9 + 45 = 54 vs. DC: 24)
[CHAT WINDOW TEXT] [Fri Jul  8 23:16:27] TEST CHAR : Reflex Save vs. Electricity : *success* : (13 + 45 = 58 vs. DC: 28)
[CHAT WINDOW TEXT] [Fri Jul  8 19:15:23] 10 AC - Chaotic Evil : Will Save vs. Mind Spells : *failure* : (3 + 1 = 4 vs. DC: 20)
[CHAT WINDOW TEXT] [Fri Jul  8 23:20:05] TEST CHAR : Reflex Save vs. Spells : *success* : (12 + 45 = 57 vs. DC: 37)


[CHAT WINDOW TEXT] [Fri Jul  8 20:22:23] Off Hand : Sneak Attack : TEST CHAR attacks 10 AC - Undead - Chaotic Evil : *hit* : (6 + 49 = 55)
[CHAT WINDOW TEXT] [Fri Jul  8 20:22:36] Off Hand : TEST CHAR attacks TRAINER : *hit* : (11 + 44 = 55)
[CHAT WINDOW TEXT] [Fri Jul  8 20:29:12] Off Hand : Flurry of Blows : Sneak Attack : TEST CHAR attacks 10 AC - Undead - Chaotic Evil : *hit* : (5 + 47 = 52)

[CHAT WINDOW TEXT] [Fri Jul  8 20:16:56] Sneak Attack : TEST CHAR attacks 10 AC DUMMY - DPS TEST : *critical hit* : (19 + 49 = 68 : Threat Roll: 10 + 49 = 59)
[CHAT WINDOW TEXT] [Fri Jul  8 20:13:36] Sneak Attack : TEST CHAR attempts Improved Knockdown on 60 AC DUMMY : *miss* : (4 + 45 = 49)

[CHAT WINDOW TEXT] [Fri Jul  8 19:23:22] TEST CHAR attacks TRAINER : *hit* : (2 + 52 = 54)

[CHAT WINDOW TEXT] [Fri Jul  8 20:26:20] Sneak Attack : TEST CHAR attempts Stunning Fist on Chaotic Evil : *miss* : (6 + 41 = 47)
[CHAT WINDOW TEXT] [Fri Jul  8 20:25:39] TEST CHAR attempts Stunning Fist on TRAINER : *failed* : (15 + 41 = 56)
[CHAT WINDOW TEXT] [Fri Jul  8 20:26:20] Sneak Attack : TEST CHAR attempts Stunning Fist on 10 AC - Undead - Chaotic Evil : *hit* : (6 + 41 = 47)
[CHAT WINDOW TEXT] [Fri Jul  8 23:20:06] 10 AC - Undead - Chaotic Evil : Fortitude Save vs. Spells : *success* : (19 + 29 = 48 vs. DC: 34)
[CHAT WINDOW TEXT] [Fri Jul  8 20:27:48] Flurry of Blows : Sneak Attack : TEST CHAR attempts Stunning Fist on 10 AC - Undead - Chaotic Evil : *hit* : (19 + 39 = 58)

[CHAT WINDOW TEXT] [Fri Jul  8 20:24:45] Flurry of Blows : TEST CHAR attacks TRAINER : *hit* : (13 + 47 = 60)

[CHAT WINDOW TEXT] [Fri Jul  8 22:14:55] Epic Black Dragon attacks TEST CHAR : *target concealed: 70%* : (9 + 47 = 56)

[CHAT WINDOW TEXT] [Sun Jul 10 23:02:11] TEST CHAR damages 10 AC DUMMY - Chaotic Evil - Boss Damage Reduction: 22 (22 Physical)
[CHAT WINDOW TEXT] [Sun Jul 10 23:02:11] 10 AC DUMMY - Chaotic Evil - Boss Damage Reduction : Damage Immunity absorbs 11 point(s) of Physical
[CHAT WINDOW TEXT] [Sun Jul 10 23:02:12] TEST CHAR damages 10 AC DUMMY - Chaotic Evil - Boss Damage Reduction: 29 (29 Physical)
[CHAT WINDOW TEXT] [Sun Jul 10 23:02:12] 10 AC DUMMY - Chaotic Evil - Boss Damage Reduction : Damage Immunity absorbs 15 point(s) of Physical

[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] TEST CHAR damages Lich Apprentice: 28 (22 Physical 6 Sonic)

[CHAT WINDOW TEXT] [Thu Jul 14 23:24:05] Experience Points Gained:  535
[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] TEST CHAR killed Lich Apprentice

[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] TEST CHAR damages Lich Apprentice: 281 (281 Physical 6 Sonic)

[CHAT WINDOW TEXT] [Mon Jul 11 01:16:34] TEST CHAR damages Adult Red Dragon: 4 (4 Physical 0 Sonic)
[CHAT WINDOW TEXT] [Mon Jul 11 01:16:34] Adult Red Dragon : Immune to Sneak Attacks.
[CHAT WINDOW TEXT] [Mon Jul 11 01:16:34] Adult Red Dragon : Damage Reduction absorbs 3 damage
[CHAT WINDOW TEXT] [Mon Jul 11 01:16:34] Adult Red Dragon : Damage Resistance absorbs 2 damage
[CHAT WINDOW TEXT] [Mon Jul 11 01:16:34] Adult Red Dragon : Damage Resistance absorbs 4 damage
[CHAT WINDOW TEXT] [Wed Jul 13 15:23:02] Adult Red Dragon : Damage Immunity absorbs 19 point(s) of Physical

[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] Adult Red Dragon damages TEST CHAR: 81 (81 Physical)

[CHAT WINDOW TEXT] [Mon Jul 11 17:52:32] Wait 10 seconds for hiding
[CHAT WINDOW TEXT] [Mon Jul 11 17:52:33] Wait 9 seconds for hiding

[CHAT WINDOW TEXT] [Wed Jul 13 00:35:34] TEST CHAR : Initiative Roll : 20 : (9 + 11 = 20)
[CHAT WINDOW TEXT] [Wed Jul 13 00:40:26] Sneak Attack : TEST CHAR attacks Badger : *hit* : (3 + 39 = 42)
[CHAT WINDOW TEXT] [Wed Jul 13 23:52:00] TEST CHAR attempts Improved Knockdown on NORTHERN ORC KING : *resisted* : (2 + 44 = 46)

[CHAT WINDOW TEXT] [Sat Jul 16 02:40:56] Done resting.
[CHAT WINDOW TEXT] [Thu Jul 14 19:29:37] TEST CHAR : Healed 2 hit points.
[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] Adult Red Dragon damages Moore Guardian: 81 (81 Physical)
[CHAT WINDOW TEXT] [Thu Jul 14 19:29:38] Moore Guardian uses Potion of Heal
[CHAT WINDOW TEXT] [Sun Jul 10 23:16:49] Adult Red Dragon damages Moore Guardian: 11 (11 Physical)
[CHAT WINDOW TEXT] [Tue Jul 19 12:33:11] TEST CHAR casting Mage Armor
[CHAT WINDOW TEXT] [Tue Jul 19 12:33:11] TEST CHAR casts Mage Armor
[CHAT WINDOW TEXT] [Tue Jul 19 12:43:07] TEST CHAR : Spell Interrupted
[CHAT WINDOW TEXT] [Tue Jul 19 14:40:28] * Divine Favor wore off *
XP DEBT: Decreased by 475 XP
Attempting to fast cast 17 spells.
[CHAT WINDOW TEXT] [Thu Jul 21 14:54:58] XP DEBT: You must pay 15550 XP, before you can start earn XP again
[CHAT WINDOW TEXT] [Wed Jul 20 22:55:50] Casting spell Bless1 at postion 15 on item with metamagic: None
[CHAT WINDOW TEXT] [Tue Jul 19 14:40:28] * Bless wore off *

[CHAT WINDOW TEXT] [Fri Jul 29 17:27:04] TEST CHAR attempts Called Shot: Leg on Dire Tiger : *hit* : (14 + 61 = 75)
[CHAT WINDOW TEXT] [Fri Jul 29 17:28:39] TEST CHAR attempts Called Shot: Arm on Dire Tiger : *critical hit* : (20 + 61 = 81 : Threat Roll: 19 + 61 = 80)

# TODO add unique
UNIQUE CREATURE KILL!
[CHAT WINDOW TEXT] [Thu Jul 28 07:43:41] Experience Points Gained:  14
[CHAT WINDOW TEXT] [Thu Jul 28 07:43:41] TEST CHAR killed Dire Tiger
TEST END

"""


def test(printer: Printer):
    parser = Parser()
    for line in test_lines.splitlines():
        parser.push_line(line)
    printer.print(parser)
    printer.change_print_mode()
    printer.change_print_mode()
