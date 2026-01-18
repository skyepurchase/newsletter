#!/bin/bash

week_num=$(date "+%U")
week_part=$(($week_num % 4))

# Change to point to your newsletter folder
mailer="$HOME/public_html/cgi-bin/newsletter/mailer.py"

for newsletter in $(find "$HOME/newsletters" -maxdepth 1 -mindepth 1); do
    issue="$newsletter/issue"

    if [ $week_part -eq 0 ]; then
        old=$(cat "$issue")
        new=$(expr $old + 1)
        echo $new > "$issue"
        python3 $mailer -q -c "$newsletter"

        if [ $? -eq 0 ]; then
            echo "$newsletter question request 1"
        else
            echo "$newsletter failed"
        fi
    elif [ $week_part -eq 1 ]; then
        python3 $mailer -q -c "$newsletter"

        if [ $? -eq 0 ]; then
            echo "$newsletter question request 2"
        else
            echo "$newsletter failed"
        fi
    elif [ $week_part -eq 2 ]; then
        python3 $mailer -a -c "$newsletter"

        if [ $? -eq 0 ]; then
            echo "$newsletter answer request 1"
        else
            echo "$newsletter failed"
        fi
    elif [ $week_part -eq 3 ]; then
        python3 $mailer -c "$newsletter"

        if [ $? -eq 0 ]; then
            echo "$newsletter published"
        else
            echo "$newsletter failed"
        fi
    else
        echo "CRITICAL: week part ($week_part) was not in mod 4."
    fi
done
