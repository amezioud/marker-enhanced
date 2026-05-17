# I rather aliasing Marker than add it to the global variable $PATH or pollute /usr/local directory
# this will make uninstalling easier and it's sufficient(for now)
alias marker="${MARKER_HOME}/bin/marker"

# default key bindings
marker_key_mark="${MARKER_KEY_MARK:-\C-k}"
marker_key_get="${MARKER_KEY_GET:-\C-@}"
marker_key_next_placeholder="${MARKER_KEY_NEXT_PLACEHOLDER:-\C-t}"

function get_cursor_position(){
  # based on a script from http://invisible-island.net/xterm/xterm.faq.html
  exec < /dev/tty
  echo -en "\033[6n" > /dev/tty
  IFS=';' read -r -d R  row col 
  # change from one-based to zero based so they work with: tput cup $row $col
  row=$((${row:2} - 1))    # strip off the esc-[
  col=$((${col} - 1))
  echo "$row $col"
}
function get_col_position(){
  echo $(get_cursor_position) | cut -f 2 -d " "
}
function get_row_position(){
  echo $(get_cursor_position) | cut -f 1 -d " "
}
function place_cursor_next_line(){
  </dev/tty echo ''
}
function place_cursor(){
  tput cup $1 $2
}
function run_marker(){
    # instruct marker to store the result (completion path) into a temporary file
    tmp_file=$(mktemp -t marker.XXXX)
    </dev/tty ${MARKER_HOME}/bin/marker get --search="$1" --stdout="$tmp_file"
    result=$(<$tmp_file)
    rm -f $tmp_file
}

if [[ -n "$ZSH_VERSION" ]]; then
    # zshell
    function _marker_get {
        # Add a letter and remove it from the buffer.
        # when using zsh autocomplete(pressing Tab), the BUFFER won't contain the trailing forward slash(which should happen when using zsh autocomplete for directories).
        # pressing a character then removing it makes sure that BUFFER contains what you see on the screen.
        BUFFER=${BUFFER}'a'
        BUFFER=${BUFFER[0,-2]}
        # get the cursor offset within the user input
        offset=${CURSOR}
        zle beginning-of-line
        # get the offset from the start of comandline prompt
        col=$(get_col_position)

        # extract the word under cursor
        word=$(echo "${BUFFER[0,offset]}" | grep -oE '[^\|]+$')
        place_cursor_next_line
        
        run_marker "$word"
        
        # append the completion path to the user buffer
        word_length=${#word}

        result_length=${#result}
        BUFFER=${BUFFER[1,$((offset-word_length))]}${result}${BUFFER[$((offset+word_length+1)),-1]}
        let "offset = offset - word_length + result_length"

        # reset the absolute and relative cursor position, note that it's necessary to get row position after marker is run, because it may be changed during marker execution
        row=$(get_row_position)
        place_cursor $(($row - 1)) $col
        CURSOR=${offset}
    }

    # Mark the written string in the command-line
    function _marker_mark_1 {
        export TMP_MARKER="$BUFFER"
        # Escape single quotes (keeping the string written by the user intact)
        ESCAPED_COMMAND=$(echo "$TMP_MARKER" | sed "s/'/'\"'\"'/g")
        BUFFER=" marker mark --command='${ESCAPED_COMMAND}'"
        zle accept-line
    }
    # Set the user written string back in the command-line
    function _marker_mark_2 {
        BUFFER="$TMP_MARKER"
        zle end-of-line
    }
    # move the cursor to the next placeholder {{name}} or complete {{name:shell-command}}
    function _move_cursor_to_next_placeholder {
        local ph_info match match_len placeholder_offset dyn_cmd tmp_file result cursor new_buffer row col
        ph_info=$(${MARKER_HOME}/bin/marker placeholder find "$BUFFER")
        if [[ -z "$ph_info" ]]; then return; fi
        placeholder_offset=${ph_info%% *}
        match=${ph_info#* }
        match_len=${#match}

        # Dynamic placeholder: {{name:shell-command}}
        dyn_cmd=$(${MARKER_HOME}/bin/marker placeholder dyn-cmd "$match")
        if [[ ! -z "$dyn_cmd" ]]; then
            zle beginning-of-line
            col=$(get_col_position)
            place_cursor_next_line
            tmp_file=$(mktemp -t marker.XXXX)
            </dev/tty ${MARKER_HOME}/bin/marker complete --command="$dyn_cmd" --stdout="$tmp_file"
            result=$(<$tmp_file)
            rm -f "$tmp_file"
            row=$(get_row_position)
            place_cursor $(($row - 1)) $col
            if [[ -z "$result" ]]; then return; fi
            result="${result%$'\n'}"
            ph_out=$(${MARKER_HOME}/bin/marker placeholder replace "$BUFFER" "$match" "$result")
            CURSOR=${ph_out%%$'\n'*}
            BUFFER=${ph_out#*$'\n'}
        else
            # Static placeholder: remove {{...}} and place cursor at its position
            ph_out=$(${MARKER_HOME}/bin/marker placeholder replace "$BUFFER" "$match" "")
            CURSOR=${ph_out%%$'\n'*}
            BUFFER=${ph_out#*$'\n'}
        fi
    }

    zle -N _marker_get
    zle -N _move_cursor_to_next_placeholder
    bindkey "$marker_key_get" _marker_get 
    bindkey "$marker_key_next_placeholder" _move_cursor_to_next_placeholder

    zle -N _marker_mark_1
    bindkey '\emm1' _marker_mark_1
    zle -N _marker_mark_2 
    bindkey '\emm2' _marker_mark_2
    bindkey -s "$marker_key_mark" '\emm1\emm2'

elif [[ -n "$BASH" ]]; then

    # move the cursor to the next placeholder {{name}} or complete {{name:shell-command}}
    function _move_cursor_to_next_placeholder {
        local ph_info match placeholder_offset dyn_cmd tmp_file result row col ph_out
        ph_info=$(${MARKER_HOME}/bin/marker placeholder find "$READLINE_LINE")
        if [[ -z "$ph_info" ]]; then return; fi
        placeholder_offset=${ph_info%% *}
        match=${ph_info#* }

        dyn_cmd=$(${MARKER_HOME}/bin/marker placeholder dyn-cmd "$match")
        if [[ ! -z "$dyn_cmd" ]]; then
            col=$(get_col_position)
            place_cursor_next_line
            tmp_file=$(mktemp -t marker.XXXX)
            </dev/tty ${MARKER_HOME}/bin/marker complete --command="$dyn_cmd" --stdout="$tmp_file"
            result=$(<$tmp_file)
            rm -f "$tmp_file"
            row=$(get_row_position)
            place_cursor $row $col
            if [[ -z "$result" ]]; then return; fi
            result="${result%$'\n'}"
            ph_out=$(${MARKER_HOME}/bin/marker placeholder replace "$READLINE_LINE" "$match" "$result")
            READLINE_POINT=${ph_out%%$'\n'*}
            READLINE_LINE=${ph_out#*$'\n'}
        else
            ph_out=$(${MARKER_HOME}/bin/marker placeholder replace "$READLINE_LINE" "$match" "")
            READLINE_POINT=${ph_out%%$'\n'*}
            READLINE_LINE=${ph_out#*$'\n'}
        fi
    }

    # Look at zsh _marker_get docstring
    # In Bash the written string will be accessed via the 'READLINE_LINE' variable, and the cursor position via 'READLINE_POINT'. Those variables are read-write
    function _marker_get {
        # pretty similar to zsh flow
        offset=${READLINE_POINT}
        READLINE_POINT=0
        col=$(get_col_position)

        word=$(echo "${READLINE_LINE:0:offset}" | grep -oE '(\w| )+$')

        run_marker "$word"

        word_length=${#word}
        result_length=${#result}
        READLINE_LINE=${READLINE_LINE:0:$((offset-word_length))}${result}${READLINE_LINE:$((offset))}
        offset=$(($offset - $word_length + $result_length))

        row=$(get_row_position)
        place_cursor $row $col
        READLINE_POINT=${offset}
    }

     # mark the written string in the command-line
    function _marker_mark_1 {
        export TMP_MARKER="$READLINE_LINE"
        # Escape single quotes (keeping the string written by the user intact)
        TMP_MARKER=$(echo "$TMP_MARKER" | sed "s/'/'\"'\"'/g")
        READLINE_LINE=" marker mark --command='${TMP_MARKER}'"
    }

    function _marker_mark_2 {
        READLINE_LINE="$TMP_MARKER"
        READLINE_POINT="${#READLINE_LINE}"
    }   

    bind -x '"'"$marker_key_get"'":_marker_get'

    bind -x '"\em1":"_marker_mark_1"'
    bind -x '"\em2":"_marker_mark_2"'
    bind '"'"$marker_key_mark"'":"\em1\n\em2"'   

    bind -x '"'"$marker_key_next_placeholder"'":"_move_cursor_to_next_placeholder"'
fi
