-- Focus the monitor in a direction, based on current screen layout (no saved monitor IDs)
local function focusScreen(dir)
  local cur = hs.mouse.getCurrentScreen() or hs.screen.mainScreen()
  local fw = hs.window.focusedWindow()
  -- desktop (Finder) counts as a window too; only trust real app windows
  if fw and fw:isStandard() then cur = fw:screen() end

  -- pick nearest screen whose center lies in that direction
  -- (toEast()/toWest() miss screens with mismatched sizes/vertical offset)
  local c = cur:frame().center
  local target, best
  for _, s in ipairs(hs.screen.allScreens()) do
    if s ~= cur then
      local sc = s:frame().center
      local dx, dy = sc.x - c.x, sc.y - c.y
      local ok = (dir == "east" and dx > 0 and math.abs(dx) >= math.abs(dy))
              or (dir == "west" and dx < 0 and math.abs(dx) >= math.abs(dy))
              or (dir == "south" and dy > 0 and math.abs(dy) > math.abs(dx))
              or (dir == "north" and dy < 0 and math.abs(dy) > math.abs(dx))
      local d = dx * dx + dy * dy
      if ok and (not best or d < best) then target, best = s, d end
    end
  end
  if not target then return end

  local center = hs.geometry.rect(target:frame()).center

  -- focus topmost window on target screen
  local focused = false
  for _, w in ipairs(hs.window.orderedWindows()) do
    if w:screen() == target and w:isStandard() and w:isVisible() then
      w:focus()
      focused = true
      break
    end
  end

  -- no windows there: click its empty desktop so keyboard focus moves too.
  -- click just under the menu bar (top-center), where icons/widgets rarely sit
  if not focused then
    local f = target:frame()
    hs.eventtap.leftClick(hs.geometry.point(f.x + f.w / 2, f.y + 2))
  end
  -- move mouse there too, so clicks/scroll land on that monitor
  hs.mouse.absolutePosition(center)
end

local mods = { "ctrl", "alt" }
hs.hotkey.bind(mods, "left",  function() focusScreen("west")  end)
hs.hotkey.bind(mods, "right", function() focusScreen("east")  end)
hs.hotkey.bind(mods, "up",    function() focusScreen("north") end)
hs.hotkey.bind(mods, "down",  function() focusScreen("south") end)
