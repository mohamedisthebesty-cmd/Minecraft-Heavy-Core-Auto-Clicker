# 🎯 Heavy Core Trigger — Minecraft Trial Chambers

> The vault opened. The loot is gone. So why does the Heavy Core still look so... clickable?

A pixel-perfect experiment for **Minecraft Trial Chambers**, built to test the community theory that the **Heavy Core** can be "opened" like a vault once you've pulled an item from it.

This tool watches a **400×400 zone at the center of your screen** and fires a **right-click** the instant it sees the Heavy Core's exact color — no mods, no memory reading, just pixels.

## ✨ What it does

- 🎯 **Real-time color tripwire** — scans the center of the screen every frame
- 🖱️ **Auto right-click** — triggers the moment RGB(86, 90, 102) appears
- ⌨️ **Global F6 hotkey** — toggle detection without alt-tabbing
- ⏱️ **5-second cooldown** — no click spam, gives the game time to react
- 📊 **Live HUD** — detection counter and status, always-on-top
- 🪟 **DPI-aware capture** — 1:1 pixel coordinates on scaled displays

## 🧪 The theory

In Trial Chambers, vaults hand out loot when you interact with them. The **Heavy Core** is the prize everyone is chasing — and the rumor is that it behaves like a vault under the right conditions. This tool is a cheap way to test that: park the core at the center of your screen, arm the trigger, and let it right-click for you the instant the target color shows up.

Whatever the result, you'll know if the pixels say "openable" or "just a rock."

## ⚙️ How it works

1. `mss` grabs a 400×400 region at screen center
2. NumPy builds an exact-match mask for **RGB(86, 90, 102)**
3. On a match, `ctypes` fires a native Windows right-click
4. The loop cools down for 5 seconds, then keeps watching

No game files are touched. It's pure screen capture + simulated input.

## 📦 Requirements

- **Windows** (uses `ctypes.windll` and Win32 mouse events)
- **Python 3.11+**
- `numpy`, `mss`

```bash
pip install -r requirements.txt
```

## 🚀 Usage

```bash
python color_trigger.py
```

1. Put the Heavy Core (or whatever you're testing) in the **center of your screen**
2. Click **STATUS: OFF** to arm the trigger — or press **F6**
3. The panel turns green and starts scanning
4. On a color match it right-clicks, bumps the counter, and cools down for 5 seconds

Press **F6** again (or click the button) to stop.

## 🔧 Tuning

Everything lives at the top of `color_trigger.py`:

| Setting | Line | Default |
| --- | --- | --- |
| Target color | `target_r/g/b` | `86, 90, 102` |
| Capture box | `box_size` | `400` px |
| Cooldown | `cooldown_sec` | `5.0` s |

Point it at a different block, a different state, or a different game entirely — just change the RGB values.

## ⚠️ Notes

- The window is **always-on-top** by design so you can watch it in-game.
- `keyboard` hooks are global — some anti-cheat / admin setups may not appreciate that.
- Automation may violate the rules of multiplayer servers. **Singleplayer or your own server only.**
- This is an experiment, not a guaranteed Heavy Core machine. Results may vary; science doesn't.

## 📜 License

MIT — do what you want, just don't blame me when the vault gives you another potion of wind charging.
