# Plugin UI & pipelines (quick ref)

Tiny cheat sheet. Full detail → `plugin.md`.

## Bootstrap pipeline

- Manager runs `bootstrap_pipeline_<name>` hooks: `(manager, state)` → optional new `state`.
- Built-in: **`permission`** (`plugins/bootstrap/bootstrap_pipelines.py`) fills `manager.context["permission_pipeline_last"]`.
- Manager calls **`permission`** twice: after bootstrap files load, after all normal plugins load.

## UI render (`ui_render`)

Implement `ui_render` / `ui_render_hook` / … signature: `(manager, window, slot, context)` → `None`, one dict, or list of dicts/widgets.

| Slot | Consumed as |
|------|-------------|
| `toolbar` | `{"type":"action","text":...,"callback":callable}` |
| `menu` | same under **Plugins** menu |
| `sidebar` | `{"widget": QWidget}` or bare widget |
| `status_widget` | widget right of status label |
| `detail` | widget below file list in details pane |
| `context_action` | `{"type":"action","target":"bundle"\|"file","text":...,"callback":...}` |

App pulls contributions once after `on_ui_ready`, then on each `refresh_ui` via `_apply_plugin_ui_slots`.

## New-plugin notice

Static scan on `.py` → `__plugin_permission_report__`. If **dangerous** or any capability tag, and path not in config `reviewed_plugin_paths`, entry lands in `manager.context["plugin_review_queue"]`; main window shows centered card until **Got it**.

Heuristics only — not a sandbox.
