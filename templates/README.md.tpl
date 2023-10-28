### Hi there 👋

I'm [Yuri](https://www.links.yuricunha.com/), I write and operate database for a living.

### 📃 Blog, playlist and wishlist

- You can check my personal [coding playlist](https://open.spotify.com/playlist/2d1HFycfFZ4XGUvO2hr240?si=34de76551a27425b), [blog](https://www.yuricunha.com/blog) and my [website](https://www.yuricunha.com/). And finally, my [wishlist](https://www.amazon.com.br/hz/wishlist/ls/3DF4K19CCQP1X)

Last blog post: [The Unconventional Bonds of Friendship and Solitude](https://www.yuricunha.com/blog/the-unconventional-bonds-of-friendship-and-solitude)

### 👷 Check out what I'm currently working on
{{range recentContributions 5}}
- [{{.Repo.Name}}]({{.Repo.URL}}){{with .Repo.Description}} - {{.}}{{end}} ({{humanize .OccurredAt}})
{{- end}}

### 📚 Books I'm reading

{{- range literalClubCurrentlyReading 5 }}
- **[{{ .Title }}{{ with .Subtitle }} - {{ . }}{{ end }}](https://literal.club/isyuricunha/book/{{.Slug}})** by _{{ range $i, $a := .Authors }}{{ if gt $i 0 }}, {{ end }}{{ $a.Name }}{{ end }}_
{{- end }}

You might want to check out my
[literal.club profile](https://literal.club/isyuricunha) as well.

### 📧 Contact

- You can see all my links [here](https://links.yuricunha.com/)