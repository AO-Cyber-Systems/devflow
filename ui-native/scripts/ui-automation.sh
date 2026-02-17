#!/bin/bash
# UI Automation helper for DevFlow using AppleScript
# Usage: ./ui-automation.sh <command> [args...]

set -e

APP_NAME="DevFlow"

case "$1" in
    launch)
        # Launch the app
        APP_PATH="${2:-/Users/justin/dev/devflow/ui-native/.build/xcode/Build/Products/Debug/DevFlow.app}"
        open "$APP_PATH"
        sleep 2
        osascript -e "tell application \"$APP_NAME\" to activate"
        echo "Launched and activated $APP_NAME"
        ;;

    list-elements)
        # List UI elements in the main window
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set entireContents to entire contents of window 1
                set results to {}
                repeat with elem in entireContents
                    set elemClass to class of elem as text
                    try
                        set elemName to name of elem
                        if elemName is not missing value then
                            set end of results to elemClass & \": \" & elemName
                        end if
                    end try
                end repeat
                return results
            end tell
        end tell"
        ;;

    list-buttons)
        # List all buttons
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set btns to every button of window 1
                set results to {}
                repeat with btn in btns
                    try
                        set btnName to name of btn
                        set btnDesc to description of btn
                        if btnName is not missing value then
                            set end of results to btnName
                        else if btnDesc is not missing value then
                            set end of results to btnDesc
                        end if
                    end try
                end repeat
                return results
            end tell
        end tell"
        ;;

    click-button)
        # Click a button by name
        BUTTON_NAME="$2"
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set frontmost to true
                delay 0.5
                -- Try to find button by name or description
                set btns to every button of window 1
                repeat with btn in btns
                    try
                        set btnName to name of btn
                        set btnDesc to description of btn
                        if btnName is \"$BUTTON_NAME\" or btnDesc is \"$BUTTON_NAME\" then
                            click btn
                            return \"Clicked: $BUTTON_NAME\"
                        end if
                    end try
                end repeat
                -- Try searching entire contents
                set allElements to entire contents of window 1
                repeat with elem in allElements
                    try
                        if class of elem is button then
                            set elemName to name of elem
                            set elemDesc to description of elem
                            if elemName is \"$BUTTON_NAME\" or elemDesc is \"$BUTTON_NAME\" then
                                click elem
                                return \"Clicked (deep): $BUTTON_NAME\"
                            end if
                        end if
                    end try
                end repeat
                return \"Button not found: $BUTTON_NAME\"
            end tell
        end tell"
        ;;

    click-menu)
        # Click a menu item: ./ui-automation.sh click-menu "DevFlow" "Quit DevFlow"
        MENU_NAME="$2"
        MENU_ITEM="$3"
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set frontmost to true
                delay 0.3
                click menu item \"$MENU_ITEM\" of menu \"$MENU_NAME\" of menu bar 1
            end tell
        end tell"
        echo "Clicked menu: $MENU_NAME > $MENU_ITEM"
        ;;

    get-text)
        # Get all static text elements
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set texts to every static text of window 1
                set results to {}
                repeat with t in texts
                    try
                        set tVal to value of t
                        if tVal is not missing value and tVal is not \"\" then
                            set end of results to tVal
                        end if
                    end try
                end repeat
                -- Also search entire contents
                set allElements to entire contents of window 1
                repeat with elem in allElements
                    try
                        if class of elem is static text then
                            set tVal to value of elem
                            if tVal is not missing value and tVal is not \"\" and tVal is not in results then
                                set end of results to tVal
                            end if
                        end if
                    end try
                end repeat
                return results
            end tell
        end tell"
        ;;

    screenshot)
        # Take a screenshot of the app window
        OUTPUT_PATH="${2:-/tmp/devflow-screenshot.png}"
        osascript -e "tell application \"$APP_NAME\" to activate"
        sleep 0.5
        screencapture -w "$OUTPUT_PATH"
        echo "Screenshot saved to: $OUTPUT_PATH"
        ;;

    sidebar-select)
        # Select an item in the sidebar by row number
        # Row mapping (may vary):
        #  1=Dashboard section header
        #  2=Dashboard
        #  3=Projects section header
        #  4=Tools, 5=Templates, 6=Docs, 7=Code
        #  8=Infrastructure section header
        #  9=Infrastructure, 10=Databases, 11=Secrets
        #  12=System section header
        #  13=Logs, 14=Config
        ROW_NUM="$2"
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                set frontmost to true
                delay 0.3
                tell outline 1 of scroll area 1 of group 1 of splitter group 1 of group 1 of window 1
                    set allRows to rows
                    if $ROW_NUM > (count of allRows) then
                        return \"Row $ROW_NUM not found (max: \" & (count of allRows) & \")\"
                    end if
                    select row $ROW_NUM
                    return \"Selected row $ROW_NUM\"
                end tell
            end tell
        end tell"
        ;;

    sidebar-list)
        # List sidebar row count
        osascript -e "
        tell application \"System Events\"
            tell process \"$APP_NAME\"
                tell outline 1 of scroll area 1 of group 1 of splitter group 1 of group 1 of window 1
                    return \"Sidebar has \" & (count of rows) & \" rows\"
                end tell
            end tell
        end tell"
        ;;

    status)
        # Get app status information
        osascript -e "
        tell application \"System Events\"
            if exists process \"$APP_NAME\" then
                tell process \"$APP_NAME\"
                    set winCount to count of windows
                    if winCount > 0 then
                        set winTitle to name of window 1
                        return \"Running - \" & winCount & \" window(s), active: \" & winTitle
                    else
                        return \"Running - no windows\"
                    end if
                end tell
            else
                return \"Not running\"
            end if
        end tell"
        ;;

    *)
        echo "DevFlow UI Automation Helper"
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  launch [app_path]     - Launch and activate DevFlow"
        echo "  list-elements         - List all UI elements in main window"
        echo "  list-buttons          - List all buttons"
        echo "  click-button <name>   - Click a button by name"
        echo "  click-menu <menu> <item> - Click a menu item"
        echo "  get-text              - Get all text content"
        echo "  screenshot [path]     - Take a screenshot"
        echo "  sidebar-select <row>  - Select sidebar row by number"
        echo "  sidebar-list          - Show sidebar row count"
        echo "  status                - Get app status"
        echo ""
        echo "Sidebar row numbers:"
        echo "  1-2=Dashboard"
        echo "  3=Templates, 4=Tools, 5=AI Agents"
        echo "  6=Documentation, 7-8=Code"
        echo "  9=Infrastructure, 10=Projects"
        echo "  11=Databases, 12=Secrets"
        echo "  13-14=Logs, 15=Settings"
        exit 1
        ;;
esac
