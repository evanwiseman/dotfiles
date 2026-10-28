-- Show dotfiles by default in the explorer and file/grep pickers.
-- Gitignored files stay hidden; toggle them with <M-i> (hidden is <M-h>).
return {
  "folke/snacks.nvim",
  opts = {
    picker = {
      sources = {
        explorer = { hidden = true },
        files = { hidden = true },
        grep = { hidden = true },
      },
    },
  },
}
