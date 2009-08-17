
#GemRB - Infinity Engine Emulator
#Copyright (C) 2003-2004 The GemRB Project
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#$Id$


#GUIINV.py - scripts to control inventory windows from GUIINV winpack

###################################################

import GemRB
import GUICommonWindows
from GUISTORE import *
from GUIDefines import *
from ie_stats import *
from ie_slots import *
from ie_spells import *
from GUICommon import CloseOtherWindow, SetColorStat, HasTOB, HasSpell
from GUICommonWindows import *

InventoryWindow = None
ItemInfoWindow = None
ItemAmountWindow = None
StackAmount = 0
ItemIdentifyWindow = None
ItemAbilitiesWindow = None
PortraitWindow = None
OptionsWindow = None
ErrorWindow = None
OldPortraitWindow = None
OldOptionsWindow = None
OverSlot = None
print # keeps the keyimporter output in two lines
PortraitTable = GemRB.LoadTableObject ("PDOLLS")

def OpenInventoryWindowClick ():
	tmp = GemRB.GetVar ("PressedPortrait")
	GemRB.GameSelectPC (tmp, True, SELECT_REPLACE)
	OpenInventoryWindow ()
	return

def OpenInventoryWindow ():
	"""Opens the inventory window."""

	global InventoryWindow, OptionsWindow, PortraitWindow
	global OldPortraitWindow, OldOptionsWindow

	if CloseOtherWindow (OpenInventoryWindow):
		if GemRB.IsDraggingItem ()==1:
			pc = GemRB.GameGetSelectedPCSingle ()
			#store the item in the inventory before window is closed
			GemRB.DropDraggedItem (pc, -3)
			#dropping on ground if cannot store in inventory
			if GemRB.IsDraggingItem ()==1:
				GemRB.DropDraggedItem (pc, -2)

		if InventoryWindow:
			InventoryWindow.Unload ()
		if OptionsWindow:
			OptionsWindow.Unload ()
		if PortraitWindow:
			PortraitWindow.Unload ()

		InventoryWindow = None
		GemRB.SetVar ("OtherWindow", -1)
		GemRB.SetVar ("MessageLabel", -1)
		GUICommonWindows.PortraitWindow = OldPortraitWindow
		OldPortraitWindow = None
		GUICommonWindows.OptionsWindow = OldOptionsWindow
		OldOptionsWindow = None
		#don't go back to multi selection mode when going to the store screen
		if not GemRB.GetVar ("Inventory"):
			GemRB.SetVisible (0,1)
			GemRB.UnhideGUI ()
			SetSelectionChangeHandler (None)
		return

	GemRB.HideGUI ()
	GemRB.SetVisible (0,0)

	GemRB.LoadWindowPack ("GUIINV", 640, 480)
	InventoryWindow = Window = GemRB.LoadWindowObject (2)
	GemRB.SetVar ("OtherWindow", InventoryWindow.ID)
	GemRB.SetVar ("MessageLabel", Window.GetControl (0x1000003f).ID )
	OldOptionsWindow = GUICommonWindows.OptionsWindow
	OptionsWindow = GemRB.LoadWindowObject (0)
	MarkMenuButton (OptionsWindow)
	SetupMenuWindowControls (OptionsWindow, 0, "OpenInventoryWindow")
	OptionsWindow.SetFrame ()
	#saving the original portrait window
	OldPortraitWindow = GUICommonWindows.PortraitWindow
	PortraitWindow = OpenPortraitWindow (0)

	#ground items scrollbar
	ScrollBar = Window.GetControl (66)
	ScrollBar.SetEvent (IE_GUI_SCROLLBAR_ON_CHANGE, "RefreshInventoryWindow")

	#Ground Item
	for i in range (5):
		Button = Window.GetControl (i+68)
		Button.SetEvent (IE_GUI_MOUSE_ENTER_BUTTON, "MouseEnterGround")
		Button.SetEvent (IE_GUI_MOUSE_LEAVE_BUTTON, "MouseLeaveGround")
		Button.SetVarAssoc ("GroundItemButton", i)
		Button.SetSprites ("STONSLOT",0,0,2,4,3)

	#major & minor clothing color
	Button = Window.GetControl (62)
	Button.SetSprites ("INVBUT",0,0,1,0,0)
	Button.SetFlags (IE_GUI_BUTTON_PICTURE,OP_OR)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS,"MajorPress")
	Button.SetTooltip (12007)

	Button = Window.GetControl (63)
	Button.SetSprites ("INVBUT",0,0,1,0,0)
	Button.SetFlags (IE_GUI_BUTTON_PICTURE,OP_OR)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS,"MinorPress")
	Button.SetTooltip (12008)

	#portrait
	Button = Window.GetControl (50)
	Button.SetState (IE_GUI_BUTTON_LOCKED)
	Button.SetFlags (IE_GUI_BUTTON_NO_IMAGE | IE_GUI_BUTTON_PICTURE, OP_SET)
	Button.SetEvent (IE_GUI_BUTTON_ON_DRAG_DROP, "OnAutoEquip")

	#encumbrance
	Label = Window.CreateLabel (0x10000043, 5,385,60,15,"NUMBER","0:",IE_FONT_ALIGN_LEFT|IE_FONT_ALIGN_TOP)
	Label = Window.CreateLabel (0x10000044, 5,455,80,15,"NUMBER","0:",IE_FONT_ALIGN_RIGHT|IE_FONT_ALIGN_TOP)

	#armor class
	Label = Window.GetControl (0x10000038)
	Label.SetTooltip (17183)

	#hp current
	Label = Window.GetControl (0x10000039)
	Label.SetTooltip (17184)

	#hp max
	Label = Window.GetControl (0x1000003a)
	Label.SetTooltip (17378)

	#info label, game paused, etc
	Label = Window.GetControl (0x1000003f)
	Label.SetText ("")

	SlotCount = GemRB.GetSlotType (-1)["Count"]
	for slot in range (SlotCount):
		SlotType = GemRB.GetSlotType (slot+1)
		if SlotType["ID"]:
			Button = Window.GetControl (SlotType["ID"])
			Button.SetEvent (IE_GUI_MOUSE_ENTER_BUTTON, "MouseEnterSlot")
			Button.SetEvent (IE_GUI_MOUSE_LEAVE_BUTTON, "MouseLeaveSlot")
			Button.SetVarAssoc ("ItemButton", slot+1)
			#keeping 2 in the original place, because it is how
			#the gui resource has it, but setting the other cycles
			Button.SetSprites ("STONSLOT",0,0,2,4,3)

	GemRB.SetVar ("TopIndex", 0)
	SetSelectionChangeHandler (UpdateInventoryWindow)
	UpdateInventoryWindow ()
	OptionsWindow.SetVisible (1)
	Window.SetVisible (3)
	PortraitWindow.SetVisible (1)
	return

def ColorDonePress ():
	"""Saves the selected colors."""

	pc = GemRB.GameGetSelectedPCSingle ()

	if ColorPicker:
		ColorPicker.Unload ()
	InventoryWindow.SetVisible (1)
	ColorTable = GemRB.LoadTableObject ("clowncol")
	PickedColor=ColorTable.GetValue (ColorIndex, GemRB.GetVar ("Selected"))
	if ColorIndex==2:
		SetColorStat (pc, IE_MAJOR_COLOR, PickedColor)
	else:
		SetColorStat (pc, IE_MINOR_COLOR, PickedColor)
	UpdateInventoryWindow ()
	return

def MajorPress ():
	"""Selects the major color."""
	global ColorIndex, PickedColor

	pc = GemRB.GameGetSelectedPCSingle ()
	ColorIndex = 2
	PickedColor = GemRB.GetPlayerStat (pc, IE_MAJOR_COLOR, 1) & 0xFF
	GetColor ()
	return

def MinorPress ():
	"""Selects the minor color."""
	global ColorIndex, PickedColor

	pc = GemRB.GameGetSelectedPCSingle ()
	ColorIndex = 3
	PickedColor = GemRB.GetPlayerStat (pc, IE_MINOR_COLOR, 1) & 0xFF
	GetColor ()
	return

def GetColor ():
	"""Opens the color selection window."""

	global ColorPicker

	ColorTable = GemRB.LoadTableObject ("clowncol")
	InventoryWindow.SetVisible (2) #darken it
	ColorPicker=GemRB.LoadWindowObject (3)
	GemRB.SetVar ("Selected",-1)
	for i in range (34):
		Button = ColorPicker.GetControl (i)
		Button.SetState (IE_GUI_BUTTON_DISABLED)
		Button.SetFlags (IE_GUI_BUTTON_PICTURE|IE_GUI_BUTTON_RADIOBUTTON,OP_OR)

	Selected = -1
	for i in range (34):
		MyColor = ColorTable.GetValue (ColorIndex, i)
		if MyColor == "*":
			break
		Button = ColorPicker.GetControl (i)
		Button.SetBAM ("COLGRAD", 2, 0, MyColor)
		if PickedColor == MyColor:
			GemRB.SetVar ("Selected",i)
			Selected = i
		Button.SetState (IE_GUI_BUTTON_ENABLED)
		Button.SetVarAssoc ("Selected",i)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "ColorDonePress")
	ColorPicker.SetVisible (1)
	return

def UpdateInventoryWindow ():
	"""Redraws the inventory window and resets TopIndex."""

	Window = InventoryWindow

	pc = GemRB.GameGetSelectedPCSingle ()
	Container = GemRB.GetContainer (pc, 1)
	ScrollBar = Window.GetControl (66)
	Count = Container['ItemCount']
	if Count<1:
		Count=1
	ScrollBar.SetVarAssoc ("TopIndex", Count)
	RefreshInventoryWindow ()
	#populate inventory slot controls
	SlotCount = GemRB.GetSlotType (-1)["Count"]
	for i in range (SlotCount):
		UpdateSlot (pc, i)
	return

def RefreshInventoryWindow ():
	"""Partial redraw without resetting TopIndex."""

	Window = InventoryWindow

	pc = GemRB.GameGetSelectedPCSingle ()

	#name
	Label = Window.GetControl (0x10000032)
	Label.SetText (GemRB.GetPlayerName (pc, 0))

	#portrait
	Button = Window.GetControl (50)
	Color1 = GemRB.GetPlayerStat (pc, IE_METAL_COLOR)
	Color2 = GemRB.GetPlayerStat (pc, IE_MINOR_COLOR)
	Color3 = GemRB.GetPlayerStat (pc, IE_MAJOR_COLOR)
	Color4 = GemRB.GetPlayerStat (pc, IE_SKIN_COLOR)
	Color5 = GemRB.GetPlayerStat (pc, IE_LEATHER_COLOR)
	Color6 = GemRB.GetPlayerStat (pc, IE_ARMOR_COLOR)
	Color7 = GemRB.GetPlayerStat (pc, IE_HAIR_COLOR)
	Button.SetPLT (GetActorPaperDoll (pc),
		Color1, Color2, Color3, Color4, Color5, Color6, Color7, 0, 0)

	anim_id = GemRB.GetPlayerStat (pc, IE_ANIMATION_ID)
	row = "0x%04X" %anim_id
	size = PortraitTable.GetValue (row, "SIZE")

	#Weapon
	slot_item = GemRB.GetSlotItem (pc, GemRB.GetEquippedQuickSlot (pc) )
	if slot_item:
		item = GemRB.GetItem (slot_item["ItemResRef"])
		if (item['AnimationType'] != ''):
			Button.SetPLT ("WP" + size + item['AnimationType'] + "INV", Color1, Color2, Color3, Color4, Color5, Color6, Color7, 0, 1)

	#Shield
	slot_item = GemRB.GetSlotItem (pc, 3)
	if slot_item:
		itemname = slot_item["ItemResRef"]
		item = GemRB.GetItem (itemname)
		if (item['AnimationType'] != ''):
			if (GemRB.CanUseItemType (SLOT_WEAPON, itemname)):
				#off-hand weapon
				Button.SetPLT ("WP" + size + item['AnimationType'] + "OIN", Color1, Color2, Color3, Color4, Color5, Color6, Color7, 0, 2)
			else:
				#shield
				Button.SetPLT ("WP" + size + item['AnimationType'] + "INV", Color1, Color2, Color3, Color4, Color5, Color6, Color7, 0, 2)

	#Helmet
	slot_item = GemRB.GetSlotItem (pc, 1)
	if slot_item:
		item = GemRB.GetItem (slot_item["ItemResRef"])
		if (item['AnimationType'] != ''):
			Button.SetPLT ("WP" + size + item['AnimationType'] + "INV", Color1, Color2, Color3, Color4, Color5, Color6, Color7, 0, 3)

	#encumbrance
	SetEncumbranceLabels ( Window, 0x10000043, 0x10000044, pc)

	#armor class
	ac = GemRB.GetPlayerStat (pc, IE_ARMORCLASS)
	#temporary solution, the dexterity bonus should be handled by the core
	#some ac bonuses are not cummulative with this AC bonus!
	ac += GemRB.GetAbilityBonus (IE_DEX, 2, GemRB.GetPlayerStat (pc, IE_DEX) )
	Label = Window.GetControl (0x10000038)
	Label.SetText (str (ac))
	Label.SetTooltip (10339)

	#hp current
	hp = GemRB.GetPlayerStat (pc, IE_HITPOINTS)
	Label = Window.GetControl (0x10000039)
	Label.SetText (str (hp))
	Label.SetTooltip (17184)

	#hp max
	hpmax = GemRB.GetPlayerStat (pc, IE_MAXHITPOINTS)
	Label = Window.GetControl (0x1000003a)
	Label.SetText (str (hpmax))
	Label.SetTooltip (17378)

	#party gold
	Label = Window.GetControl (0x10000040)
	Label.SetText (str (GemRB.GameGetPartyGold ()))

	#class
	ClassTitle = GetActorClassTitle (pc)
	Label = Window.GetControl (0x10000042)
	Label.SetText (ClassTitle)

	Button = Window.GetControl (62)
	Color = GemRB.GetPlayerStat (pc, IE_MAJOR_COLOR, 1) & 0xFF
	Button.SetBAM ("COLGRAD", 0, 0, Color)

	Button = Window.GetControl (63)
	Color = GemRB.GetPlayerStat (pc, IE_MINOR_COLOR, 1) & 0xFF
	Button.SetBAM ("COLGRAD", 0, 0, Color)

	#update ground inventory slots
	Container = GemRB.GetContainer (pc, 1)
	TopIndex = GemRB.GetVar ("TopIndex")
	for i in range (5):
		Button = Window.GetControl (i+68)
		if GemRB.IsDraggingItem ()==1:
			Button.SetState (IE_GUI_BUTTON_SECOND)
		else:
			Button.SetState (IE_GUI_BUTTON_ENABLED)
		Button.SetEvent (IE_GUI_BUTTON_ON_DRAG_DROP, "OnDragItemGround")
		Slot = GemRB.GetContainerItem (pc, i+TopIndex)

		if Slot == None:
			Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "")
			Button.SetEvent (IE_GUI_BUTTON_ON_RIGHT_PRESS, "")
			Button.SetEvent (IE_GUI_BUTTON_ON_SHIFT_PRESS, "")
		else:
			Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "OnDragItemGround")
			Button.SetEvent (IE_GUI_BUTTON_ON_RIGHT_PRESS, "OpenGroundItemInfoWindow")
			Button.SetEvent (IE_GUI_BUTTON_ON_SHIFT_PRESS, "OpenGroundItemAmountWindow")

		UpdateInventorySlot (pc, Button, Slot, "ground")

	#making window visible/shaded depending on the pc's state
	Window.SetVisible (1)
	return

def UpdateSlot (pc, slot):
	"""Updates a specific slot."""

	Window = InventoryWindow
	SlotType = GemRB.GetSlotType (slot+1, pc)
	ControlID = SlotType["ID"]

	if not ControlID:
		return

	if GemRB.IsDraggingItem ()==1:
		#get dragged item
		drag_item = GemRB.GetSlotItem (0,0)
		itemname = drag_item["ItemResRef"]
		drag_item = GemRB.GetItem (itemname)
	else:
		itemname = ""

	Button = Window.GetControl (ControlID)
	slot_item = GemRB.GetSlotItem (pc, slot+1)

	Button.SetEvent (IE_GUI_BUTTON_ON_DRAG_DROP, "OnDragItem")
	Button.SetFlags (IE_GUI_BUTTON_NO_IMAGE, OP_NAND)
	UpdateInventorySlot (pc, Button, slot_item, "inventory")
	
	if slot_item:
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "OnDragItem")
		Button.SetEvent (IE_GUI_BUTTON_ON_RIGHT_PRESS, "OpenItemInfoWindow")
		Button.SetEvent (IE_GUI_BUTTON_ON_SHIFT_PRESS, "OpenItemAmountWindow")
		Button.SetEvent (IE_GUI_BUTTON_ON_DOUBLE_PRESS, "OpenItemAmountWindow")
	else:
		if SlotType["ResRef"]=="*":
			Button.SetBAM ("",0,0)
			Button.SetTooltip (SlotType["Tip"])
			itemname = ""
		elif SlotType["ResRef"]=="":
			Button.SetBAM ("",0,0)
			Button.SetFlags (IE_GUI_BUTTON_NO_IMAGE, OP_OR)
			Button.SetTooltip ("")
			itemname = ""
		else:
			Button.SetBAM (SlotType["ResRef"],0,0)
			Button.SetTooltip (SlotType["Tip"])

		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "")
		Button.SetEvent (IE_GUI_BUTTON_ON_RIGHT_PRESS, "")
		Button.SetEvent (IE_GUI_BUTTON_ON_SHIFT_PRESS, "")
		Button.SetEvent (IE_GUI_BUTTON_ON_DOUBLE_PRESS, "")

	if OverSlot == slot+1:
		if GemRB.CanUseItemType (SlotType["Type"], itemname):
			Button.SetState (IE_GUI_BUTTON_SELECTED)
		else:
			Button.SetState (IE_GUI_BUTTON_ENABLED)
	else:
		if (SlotType["Type"]&SLOT_INVENTORY) or not GemRB.CanUseItemType (SlotType["Type"], itemname):
			Button.SetState (IE_GUI_BUTTON_ENABLED)
		else:
			Button.SetState (IE_GUI_BUTTON_SECOND)

		if slot_item and (GemRB.GetEquippedQuickSlot (pc)==slot+1 or GemRB.GetEquippedAmmunition (pc)==slot+1):
			Button.SetState (IE_GUI_BUTTON_THIRD)

	return

def OnDragItemGround ():
	"""Drops and item to the ground."""

	pc = GemRB.GameGetSelectedPCSingle ()

	slot = GemRB.GetVar ("GroundItemButton") + GemRB.GetVar ("TopIndex")
	if GemRB.IsDraggingItem ()==0:
		slot_item = GemRB.GetContainerItem (pc, slot)
		item = GemRB.GetItem (slot_item["ItemResRef"])
		GemRB.DragItem (pc, slot, item["ItemIcon"], 0, 1) #container
	else:
		GemRB.DropDraggedItem (pc, -2) #dropping on ground

	UpdateInventoryWindow ()
	return

def OnAutoEquip ():
	"""Auto-equips equipment if possible."""

	if GemRB.IsDraggingItem ()!=1:
		return

	pc = GemRB.GameGetSelectedPCSingle ()

	#-1 : drop stuff in equipable slots (but not inventory)
	GemRB.DropDraggedItem (pc, -1)

	if GemRB.IsDraggingItem ()==1:
		GemRB.PlaySound ("GAM_47") #failed equip

	UpdateInventoryWindow ()
	return

def OnDragItem ():
	"""Updates dragging."""

	if GemRB.IsDraggingItem()==2:
		return

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")

	if not GemRB.IsDraggingItem ():
		slot_item = GemRB.GetSlotItem (pc, slot)
		item = GemRB.GetItem (slot_item["ItemResRef"])
		GemRB.DragItem (pc, slot, item["ItemIcon"], 0, 0)
	else:
		SlotType = GemRB.GetSlotType (slot, pc)
		#special monk check
		if GemRB.GetPlayerStat (pc, IE_CLASS)==0x14:
			#offhand slot mark
			if SlotType["Effects"]==TYPE_OFFHAND:
				SlotType["ResRef"]=""
				GemRB.DisplayString (61355, 0xffffff)

		if SlotType["ResRef"]!="":
			GemRB.DropDraggedItem (pc, slot)

	UpdateInventoryWindow ()
	return

def OnDropItemToPC ():
	"""Gives an item to another character."""

	pc = GemRB.GetVar ("PressedPortrait")

	#-3 : drop stuff in inventory (but not equippable slots)
	GemRB.DropDraggedItem (pc, -3)
	if GemRB.IsDraggingItem ()==1:
		if HasTOB ():
			GemRB.DisplayString (61794,0xfffffff)
		else:
			GemRB.DisplayString (17999,0xfffffff)

	UpdateInventoryWindow ()
	return

def DecreaseStackAmount ():
	"""Decreases the split size."""

	Text = ItemAmountWindow.GetControl (6)
	Amount = Text.QueryText ()
	number = int ("0"+Amount)-1
	if number<1:
		number=1
	Text.SetText (str (number))
	return

def IncreaseStackAmount ():
	"""Increases the split size."""

	Text = ItemAmountWindow.GetControl (6)
	Amount = Text.QueryText ()
	number = int ("0"+Amount)+1
	if number>StackAmount:
		number=StackAmount
	Text.SetText (str (number))
	return

def DragItemAmount ():
	"""Drag a split item."""

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	slot_item = GemRB.GetSlotItem (pc, slot)
	Text = ItemAmountWindow.GetControl (6)
	Amount = Text.QueryText ()
	item = GemRB.GetItem (slot_item["ItemResRef"])
	GemRB.DragItem (pc, slot, item["ItemIcon"], int ("0"+Amount), 0)
	OpenItemAmountWindow ()
	return

def OpenItemAmountWindow ():
	"""Open the split window."""

	global ItemAmountWindow, StackAmount

	if ItemAmountWindow != None:
		if ItemAmountWindow:
			ItemAmountWindow.Unload ()
		ItemAmountWindow = None

		GemRB.SetRepeatClickFlags (GEM_RK_DISABLE, OP_OR)
		return

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")

	if GemRB.IsDraggingItem ()==1:
		GemRB.DropDraggedItem (pc, slot)
		# disallow splitting while holding split items (double splitting)
		if GemRB.IsDraggingItem () == 1:
			UpdateSlot (pc, slot-1)
			return
	else:
		return

	GemRB.SetRepeatClickFlags (GEM_RK_DISABLE, OP_NAND)

	slot_item = GemRB.GetSlotItem (pc, slot)
	ResRef = slot_item['ItemResRef']
	item = GemRB.GetItem (ResRef)

	if slot_item:
		StackAmount = slot_item["Usages0"]
	else:
		StackAmount = 0
	if StackAmount<=1:
		UpdateSlot (pc, slot-1)
		return

	ItemAmountWindow = Window = GemRB.LoadWindowObject (4)
	# item icon
	Icon = Window.GetControl (0)
	Icon.SetFlags (IE_GUI_BUTTON_PICTURE | IE_GUI_BUTTON_NO_IMAGE, OP_SET)
	Icon.SetItemIcon (ResRef)

	# item amount
	Text = Window.GetControl (6)
	Text.SetText (str (StackAmount//2) )
	Text.SetStatus (IE_GUI_EDIT_NUMBER|IE_GUI_CONTROL_FOCUSED)

	# Decrease
	Button = Window.GetControl (4)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS,"DecreaseStackAmount")

	# Increase
	Button = Window.GetControl (3)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS,"IncreaseStackAmount")

	# Done
	Button = Window.GetControl (2)
	Button.SetText (11973)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "DragItemAmount")
	Button.SetFlags (IE_GUI_BUTTON_DEFAULT, OP_OR)

	# Cancel
	Button = Window.GetControl (1)
	Button.SetText (13727)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "OpenItemAmountWindow")
	Button.SetFlags (IE_GUI_BUTTON_CANCEL, OP_OR)

	Window.ShowModal (MODAL_SHADOW_GRAY)
	return

def DrinkItemWindow ():
	"""Drink?"""

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	# the drink item header is always the first
	GemRB.UseItem (pc, slot, 0)
	CloseItemInfoWindow ()
	return

def OpenErrorWindow (strref):
	"""Opens the error window and displays the string."""

	global ErrorWindow
	pc = GemRB.GameGetSelectedPCSingle ()

	ErrorWindow = Window = GemRB.LoadWindowObject (7)
	Button = Window.GetControl (0)
	Button.SetText (11973)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "CloseErrorWindow")
	Button.SetFlags (IE_GUI_BUTTON_DEFAULT, OP_OR)

	TextArea = Window.GetControl (3)
	TextArea.SetText (strref)
	Window.ShowModal (MODAL_SHADOW_GRAY)
	return

def CloseErrorWindow ():
	if ErrorWindow:
		ErrorWindow.Unload ()
	UpdateInventoryWindow ()
	return

def ReadItemWindow ():
	"""Tries to learn the mage scroll."""

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	ret = 0

	slot_item = GemRB.GetSlotItem (pc, slot)
	spell_ref = GemRB.GetItem (slot_item['ItemResRef'], pc)['Spell']
	spell = GemRB.GetSpell (spell_ref)
	if spell:
		# can we learn more spells of this level?
		spell_count = GemRB.GetKnownSpellsCount (pc, IE_SPELL_TYPE_WIZARD, spell['SpellLevel']-1)
		if spell_count > GemRB.GetAbilityBonus (IE_INT, 2, GemRB.GetPlayerStat (pc, IE_INT)):
			ret = LSR_FULL
			strref = 32097
		else:
			if GemRB.LearnSpell (pc, spell_ref, LS_STATS|LS_ADDXP):
				ret = LSR_FAILED
				strref = 10831 # failure
			else:
				strref = 10830 # success
			GemRB.RemoveItem (pc, slot)
	else:
		print "WARNING: invalid spell header in item", slot_item['ItemResRef']
		CloseItemInfoWindow ()
		return -1

	CloseItemInfoWindow ()
	OpenErrorWindow (strref)

	return ret

def OpenItemWindow ():
	"""Displays information about an item."""

	#close inventory
	GemRB.SetVar ("Inventory", 1)
	if ItemInfoWindow:
		ItemInfoWindow.Unload ()
	OpenInventoryWindow ()
	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	slot_item = GemRB.GetSlotItem (pc, slot)
	ResRef = slot_item['ItemResRef']
	#the store will have to reopen the inventory
	GemRB.EnterStore (ResRef)
	return

def DialogItemWindow ():
	"""Converse with an item. (Lilacor?)"""

	if ItemInfoWindow:
		ItemInfoWindow.Unload ()
	OpenInventoryWindow ()
	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	slot_item = GemRB.GetSlotItem (pc, slot)
	ResRef = slot_item['ItemResRef']
	item = GemRB.GetItem (ResRef)
	dialog=item["Dialog"]
	GemRB.ExecuteString ("StartDialogOverride(\""+dialog+"\",Myself,0,0,1)", pc)
	return

def IdentifyUseSpell ():
	"""Identifies an item with a memorized spell."""

	global ItemIdentifyWindow

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	if ItemIdentifyWindow:
		ItemIdentifyWindow.Unload ()
	GemRB.HasSpecialSpell (pc, 1, 1)
	if ItemInfoWindow:
		ItemInfoWindow.Unload ()
	GemRB.ChangeItemFlag (pc, slot, IE_INV_ITEM_IDENTIFIED, OP_OR)
	OpenItemInfoWindow ()
	return

def IdentifyUseScroll ():
	"""Identifies an item with a scroll."""

	global ItemIdentifyWindow

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	if ItemIdentifyWindow:
		ItemIdentifyWindow.Unload ()
	if ItemInfoWindow:
		ItemInfoWindow.Unload ()
	if GemRB.HasSpecialItem (pc, 1, 1):
		GemRB.ChangeItemFlag (pc, slot, IE_INV_ITEM_IDENTIFIED, OP_OR)
	OpenItemInfoWindow ()
	return

def CloseIdentifyItemWindow ():
	if ItemIdentifyWindow:
		ItemIdentifyWindow.Unload ()
	return

def IdentifyItemWindow ():
	global ItemIdentifyWindow

	pc = GemRB.GameGetSelectedPCSingle ()

	ItemIdentifyWindow = Window = GemRB.LoadWindowObject (9)
	Button = Window.GetControl (0)
	Button.SetText (17105)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "IdentifyUseSpell")
	if not GemRB.HasSpecialSpell (pc, 1, 0):
		Button.SetState (IE_GUI_BUTTON_DISABLED)

	Button = Window.GetControl (1)
	Button.SetText (17106)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "IdentifyUseScroll")
	if not GemRB.HasSpecialItem (pc, 1, 0):
		Button.SetState (IE_GUI_BUTTON_DISABLED)

	Button = Window.GetControl (2)
	Button.SetText (13727)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "CloseIdentifyItemWindow")
	Button.SetFlags (IE_GUI_BUTTON_CANCEL, OP_OR)

	TextArea = Window.GetControl (3)
	TextArea.SetText (19394)
	Window.ShowModal (MODAL_SHADOW_GRAY)
	return

def DoneAbilitiesItemWindow ():
	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	GemRB.SetupQuickSlot (pc, -1, slot, GemRB.GetVar ("Ability") )
	CloseAbilitiesItemWindow ()
	return

def CloseAbilitiesItemWindow ():
	global ItemAbilitiesWindow

	if ItemAbilitiesWindow:
		ItemAbilitiesWindow.Unload ()
		ItemAbilitiesWindow = None
	return

def AbilitiesItemWindow ():
	global ItemAbilitiesWindow

	ItemAbilitiesWindow = Window = GemRB.LoadWindowObject (6)

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	slot_item = GemRB.GetSlotItem (pc, slot)
	item = GemRB.GetItem (slot_item["ItemResRef"])
	Tips = item["Tooltips"]

	GemRB.SetVar ("Ability", 0)
	for i in range(3):
		Button = Window.GetControl (i+1)
		Button.SetSprites ("GUIBTBUT",i,0,1,2,0)
		Button.SetFlags (IE_GUI_BUTTON_RADIOBUTTON, OP_OR)
		Button.SetVarAssoc ("Ability",i)
		Text = Window.GetControl (i+0x10000003)
		if i<len(Tips):
			Button.SetItemIcon (slot_item['ItemResRef'],i+6)
			Text.SetText (Tips[i])
		else:
			#disable button
			Button.SetItemIcon ("",3)
			Text.SetText ("")
			Button.SetState (IE_GUI_BUTTON_DISABLED)

	TextArea = Window.GetControl (8)
	TextArea.SetText (11322)

	Button = Window.GetControl (7)
	Button.SetText (11973)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "DoneAbilitiesItemWindow")
	Button.SetFlags (IE_GUI_BUTTON_DEFAULT, OP_OR)

	Button = Window.GetControl (10)
	Button.SetText (13727)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "CloseAbilitiesItemWindow")
	Button.SetFlags (IE_GUI_BUTTON_CANCEL, OP_OR)
	Window.ShowModal (MODAL_SHADOW_GRAY)
	return

def CloseItemInfoWindow ():
	if ItemInfoWindow:
		ItemInfoWindow.Unload ()
	UpdateInventoryWindow ()
	return

def DisplayItem (itemresref, type):
	global ItemInfoWindow

	item = GemRB.GetItem (itemresref)
	ItemInfoWindow = Window = GemRB.LoadWindowObject (5)

	#item icon
	Button = Window.GetControl (2)
	Button.SetFlags (IE_GUI_BUTTON_PICTURE, OP_OR)
	Button.SetItemIcon (itemresref,0)
	Button.SetState (IE_GUI_BUTTON_LOCKED)

	#middle button
	Button = Window.GetControl (4)
	Button.SetText (11973)
	Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "CloseItemInfoWindow")
	Button.SetFlags (IE_GUI_BUTTON_CANCEL, OP_OR)

	#textarea
	Text = Window.GetControl (5)
	if (type&2):
		text = item["ItemDesc"]
	else:
		text = item["ItemDescIdentified"]
	Text.SetText (text)

	#left button
	Button = Window.GetControl (8)
	select = (type&1) and (item["Function"]&8)

	if type&2:
		Button.SetText (14133)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "IdentifyItemWindow")
	elif select:
		Button.SetText (11960)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "AbilitiesItemWindow")
	else:
		Button.SetState (IE_GUI_BUTTON_LOCKED)
		Button.SetFlags (IE_GUI_BUTTON_NO_IMAGE, OP_SET)

	#description icon
	Button = Window.GetControl (7)
	Button.SetFlags (IE_GUI_BUTTON_PICTURE | IE_GUI_BUTTON_CENTER_PICTURES, OP_OR)
	Button.SetItemIcon (itemresref,2)
	Button.SetState (IE_GUI_BUTTON_LOCKED)

	#right button
	Button = Window.GetControl (9)
	drink = (type&1) and (item["Function"]&1)
	read = (type&1) and (item["Function"]&2)
	container = (type&1) and (item["Function"]&4)
	dialog = (type&1) and (item["Dialog"]!="")
	familiar = (type&1) and (item["Type"] == 38)
	if drink:
		Button.SetText (19392)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "DrinkItemWindow")
	elif read and not CannotLearnSlotSpell ():
		Button.SetText (17104)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "ReadItemWindow")
	elif container:
		Button.SetText (44002)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "OpenItemWindow")
	elif dialog:
		Button.SetText (item["DialogName"])
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "DialogItemWindow")
	elif familiar:
		Button.SetText (4373)
		Button.SetEvent (IE_GUI_BUTTON_ON_PRESS, "ReleaseFamiliar")
	else:
		Button.SetState (IE_GUI_BUTTON_LOCKED)
		Button.SetFlags (IE_GUI_BUTTON_NO_IMAGE, OP_SET)

	Text = Window.GetControl (0x10000000)
	Label = Window.GetControl (0x1000000b)
	if (type&2):
		text = item["ItemName"]
		label = 17108
	else:
		text = item["ItemNameIdentified"]
		label = ""

	Text.SetText (text)
	Label.SetText (label)

	ItemInfoWindow.ShowModal (MODAL_SHADOW_GRAY)
	return

def CannotLearnSlotSpell ():
	pc = GemRB.GameGetSelectedPCSingle ()

	# disqualify sorcerors immediately
	if GemRB.GetPlayerStat (pc, IE_CLASS) == 19:
		return LSR_STAT

	slot_item = GemRB.GetSlotItem (pc, GemRB.GetVar ("ItemButton"))
	spell_ref = GemRB.GetItem (slot_item['ItemResRef'], pc)['Spell']
	spell = GemRB.GetSpell (spell_ref)

	# maybe she already knows this spell
	if HasSpell (pc, IE_SPELL_TYPE_WIZARD, spell['SpellLevel']-1, spell_ref) != -1:
		return LSR_KNOWN

	# level check (needs enough intelligence for this level of spell)
	dumbness = GemRB.GetPlayerStat (pc, IE_INT)
	if spell['SpellLevel'] > GemRB.GetAbilityBonus (IE_INT, 1, dumbness):
		return LSR_LEVEL

	return 0

def OpenItemInfoWindow ():
	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	slot_item = GemRB.GetSlotItem (pc, slot)
	item = GemRB.GetItem (slot_item["ItemResRef"])

	#auto identify when lore is high enough
	if item["LoreToID"]<=GemRB.GetPlayerStat (pc, IE_LORE):
		GemRB.ChangeItemFlag (pc, slot, IE_INV_ITEM_IDENTIFIED, OP_OR)
		slot_item["Flags"] |= IE_INV_ITEM_IDENTIFIED
		UpdateInventoryWindow ()

	if slot_item["Flags"] & IE_INV_ITEM_IDENTIFIED:
		value = 1
	else:
		value = 3
	DisplayItem (slot_item["ItemResRef"], value)
	return

def OpenGroundItemInfoWindow ():
	global ItemInfoWindow

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("TopIndex") + GemRB.GetVar ("GroundItemButton")
	slot_item = GemRB.GetContainerItem (pc, slot)

	#the ground items are only displayable
	if slot_item["Flags"] & IE_INV_ITEM_IDENTIFIED:
		value = 0
	else:
		value = 2
	DisplayItem (slot_item["ItemResRef"], value)
	return

def MouseEnterSlot ():
	global OverSlot

	pc = GemRB.GameGetSelectedPCSingle ()
	OverSlot = GemRB.GetVar ("ItemButton")
	if GemRB.IsDraggingItem ()==1:
		UpdateSlot (pc, OverSlot-1)
	return

def MouseLeaveSlot ():
	global OverSlot

	pc = GemRB.GameGetSelectedPCSingle ()
	slot = GemRB.GetVar ("ItemButton")
	if slot == OverSlot or not GemRB.IsDraggingItem ():
		OverSlot = None
	UpdateSlot (pc, slot-1)
	return

def MouseEnterGround ():
	Window = InventoryWindow
	i = GemRB.GetVar ("GroundItemButton")
	Button = Window.GetControl (i+68)
	if GemRB.IsDraggingItem ()==1:
		Button.SetState (IE_GUI_BUTTON_SELECTED)
	return

def MouseLeaveGround ():
	Window = InventoryWindow
	i = GemRB.GetVar ("GroundItemButton")
	Button = Window.GetControl (i+68)
	if GemRB.IsDraggingItem ()==1:
		Button.SetState (IE_GUI_BUTTON_SECOND)
	return

###################################################
#End of file GUIINV.py
