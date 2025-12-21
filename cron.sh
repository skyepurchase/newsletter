#!/bin/bash

week_num=$(date "+%U");
week_part=$(($week_num % 4))

# Change to point to your newsletter folder
newsletter_dir="$HOME/public_html/cgi-bin/newsletter"

for newsletter in /home/atp45/newsletters/*; do
    config="$newsletter/config.yaml";
    issue="$newsletter/issue";

    if [ $week_part -eq 3 ]; then
        python3 "$newsletter_dir/mailer.py" -c "$config";
        echo "INFO $(date): $newsletter newsletter published";
    elif [ $week_part -eq 0 ]; then
        old=$(cat "$issue");
        new=$(expr $old + 1);
        echo $new > "$issue";
        python3 "$newsletter_dir/mailer.py" -q -c "$config";
        echo "INFO $(date): $newsletter newsletter question request 1";
    elif [ $week_part -eq 1 ]; then
        python3 "$newsletter_dir/mailer.py" -q -c "$config";
        echo "INFO $(date): $newsletter newsletter question request 2";
    elif [ $week_part -eq 2 ]; then
        python3 "$newsletter_dir/mailer.py" -a -c "$config";
        echo "INFO $(date): $newsletter newsletter answer request";
    else
        echo "CRITICAL: week part ($week_part) was not in mod 4.";
    fi;
done;
