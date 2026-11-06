-- Show dotfiles by default in the explorer and file/grep pickers, and gitignored
-- files in the explorer too. Toggle hidden with <M-h> and ignored with <M-i>.
return {
  "folke/snacks.nvim",
  opts = {
    picker = {
      sources = {
        explorer = { hidden = true, ignored = true },
        files = { hidden = true },
        grep = { hidden = true },
      },
    },
  },
}
