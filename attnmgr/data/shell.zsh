# source: https://github.com/ihashacks/notifyosd.zsh/blob/master/notifyosd.zsh
# commands to ignore
cmdignore=(htop tmux top vim less)

# set gt 0 to enable GNU units for time results
# gnuunits=0
gnuunits=1

USRDIR=/run/current-system/profile




# end and compare timer, notify-send if needed
function notifyosd-precmd()
{
	retval=$?
  if [[ ${cmdignore[(r)$cmd_basename]} == $cmd_basename ]]
  then
      return
  else
      if [ ! -z "$cmd" ]
      then
          cmd_end=`date +%s`
          ((cmd_secs=$cmd_end - $cmd_start))
      fi
      if [ $retval -gt 0 ]
      then
			    cmdstat="with warning"
			    sndstat="$USRDIR/share/sounds/gnome/default/alerts/sonar.ogg"
			    urgency="critical"
		  else
          cmdstat="successfully"
			    sndstat="$USRDIR/share/sounds/gnome/default/alerts/glass.ogg"
			    urgency="normal"
      fi
      if [ ! -z "$cmd" -a $cmd_secs -gt 10 ]
      then
			    if [ $gnuunits -gt 0 ]
          then
				      cmd_time=$(units "$cmd_secs seconds" "centuries;years;months;weeks;days;hours;minutes;seconds" | \
						                 sed -e 's/\ +/\,/g' -e s'/\t//')
			    else
				      cmd_time="$cmd_secs seconds"
			    fi
          if [ ! -z $SSH_TTY ]
          then
              notify-send -i utilities-terminal \
						              -u $urgency "$cmd_basename on $(hostname) completed $cmdstat" "\"$cmd\" took $cmd_time"
          else
              notify-send -i utilities-terminal \
						              -u $urgency "$cmd_basename completed $cmdstat" "\"$cmd\" took $cmd_time"
          fi

          if [ $TERM = "screen" ]
          then
              local SESSION="${STY#*.}"
              if [ "x$SSH_CONNECTION" = "x" ]
              then
                  reqattn.py rsshscreen session "$SESSION" timetaken "$cmd_secs" cmd "$cmd" retval "$retval"
              else
                  SERVERIP=$(echo $SSH_CONNECTION | cut -f3 -d' ')
                  echo rsshscreen session "$SESSION" timetaken "$cmd_secs" cmd "$cmd" retval "$retval" server "$SERVERIP" user "$USER" > ~/.attnmgr/$SESSION
              fi
          else
              ./reqattn.py xwin winid "$(xdotool search --pid $PPID | head -1 )" timetaken "$cmd_secs" cmd "$cmd" retval "$retval"
          fi
          if whence -p play >& /dev/null
          then
						  play -q $sndstat
          fi
      fi
      unset cmd
  fi
}

# make sure this plays nicely with any existing precmd
precmd_functions+=( notifyosd-precmd )

# get command name and start the timer
function notifyosd-preexec()
{
    cmd=$1
    cmd_basename=${${cmd:s/sudo //}[(ws: :)1]}
    cmd_start=`date +%s`
}

# make sure this plays nicely with any existing preexec
preexec_functions+=( notifyosd-preexec )
