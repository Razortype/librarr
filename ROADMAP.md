# Roadmap

This is a living document. Priorities change with feedback.

## v0.1 — MVP (Goal: 4-8 weeks)

Goal: a single user can add a book by title, librarr finds it, downloads it, and adds it to a Calibre library.

- [ ] Project skeleton, Docker setup, CI
- [ ] Database schema (Book, Author, Edition, Download, Settings)
- [ ] Cloud metadata client (talk to librarr-cloud)
- [ ] Local metadata fallback (Open Library direct, no LLM)
- [ ] Prowlarr integration (search across user's indexers)
- [ ] qBittorrent integration (download client)
- [ ] Calibre library integration (post-download import)
- [ ] Web UI: add book, search, monitor, library view
- [ ] Confidence scores in UI (show uncertainty, ask user when low)
- [ ] Demo video, README cleanup, public launch

## v0.2 — *arr stack parity

- [ ] SABnzbd / NZBGet support (Usenet)
- [ ] Transmission, Deluge, rTorrent support
- [ ] Quality profiles (preferred formats: epub, mobi, m4b)
- [ ] Author monitoring (auto-add new releases)
- [ ] Multi-edition handling (multiple formats per book)
- [ ] Notification systems (Discord, Telegram, Apprise)

## v0.3 — Audiobooks

- [ ] Audiobook detection and separate library
- [ ] Audnexus / Audible metadata
- [ ] Audiobookshelf integration
- [ ] M4B chapter handling

## v0.4 — Power user

- [ ] OPDS feed for ereader sync
- [ ] Kobo / Kindle integration
- [ ] Multi-user support (with auth)
- [ ] Custom metadata sources (BYO MCP server)
- [ ] BYO LLM key for cloud bypass

## Future considerations

- Magazines, comics — only if community demand is loud
- Mobile app — only if web UI usage justifies it
- Self-hosted cloud component — documented self-host path

## Non-goals

- Replicating LazyLibrarian's "everything for everyone" feature scope
- Becoming a Calibre alternative — librarr orchestrates, Calibre owns the library
- Built-in indexers (use Prowlarr; we're not in that business)
