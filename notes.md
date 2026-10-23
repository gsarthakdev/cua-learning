See every matching window ID + title:
```bash
xdotool search --onlyvisible --name "LibreOffice Writer" \
  | while read -r id; do
      echo "Window ID: $id"
      xdotool getwindowname "$id"
      echo "---"
    done
```