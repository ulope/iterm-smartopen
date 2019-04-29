import textwrap
from subprocess import check_call

import click
import pasteboard
from applescript import AppleScript, ScriptError, AEType


_GET_FRONT_APP_SCRIPT = AppleScript(textwrap.dedent("""\
    tell application "System Events"
        set frontmostApplicationName to name of 1st process whose frontmost is true
    end tell
    return frontmostApplicationName
"""))

_SET_FRONT_APP_SCRIPT = AppleScript(textwrap.dedent("""\
    on run {frontmostApplicationName}
        tell application frontmostApplicationName to activate
    end run
"""))
#         display dialog dialogText buttons {"Open", "Edit", "Copy"} default button "Copy" cancel button "Edit" with icon file ((path to application "Iterm2" as text) & "Contents:Resources:AppIcon.icns")
_SHOW_DIALOG_SCRIPT = AppleScript(textwrap.dedent("""\
    on run {dialogText}
        activate
        display alert dialogText message "Enter: Copy, Esc: Edit, Space: Open" as informational buttons {"Open", "Edit", "Copy"} default button "Copy" cancel button "Edit" giving up after 30
    end run
"""))

_EVENT_BUTTON_HIT = AEType(b'bhit')
_EVENT_GAVE_UP = AEType(b'gvau')


@click.command()
@click.argument('obj', type=str)
def main(obj):
    front_app = _GET_FRONT_APP_SCRIPT.run()

    try:
        res = _SHOW_DIALOG_SCRIPT.run(f"Choose action for '{obj}'")
        if res.get(_EVENT_GAVE_UP):
            print('no selection')
            return
        selected_action = res.get(_EVENT_BUTTON_HIT)
    except ScriptError:
        # User canceled - i.e. want's to edit the link
        selected_action = 'Edit'

    if selected_action == 'Copy':
        pasteboard.Pasteboard().set_contents(obj, pasteboard.String)
        _SET_FRONT_APP_SCRIPT.run(front_app)
    elif selected_action in {'Open', 'Edit'}:
        command = ['/usr/bin/open']
        if selected_action == 'Edit':
            command.append('-t')
        command.append(obj)
        check_call(command)
    else:
        raise ValueError(f'Invalid selection: {selected_action}')


if __name__ == "__main__":
    main()
