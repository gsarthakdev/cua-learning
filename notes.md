See every matching window ID + title:
```bash
xdotool search --onlyvisible --name "LibreOffice Writer" \
  | while read -r id; do
      echo "Window ID: $id"
      xdotool getwindowname "$id"
      echo "---"
    done
```

Claude proposed action example:
```json
{
  "action": "type",
  "text": "Hello from my Python computer-use executor!",
  "key": "",
  "x": 0,
  "y": 0
}
```