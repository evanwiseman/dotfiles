return {
  "neovim/nvim-lspconfig",
  opts = {
    inlay_hints = { enabled = false },
    servers = {
      -- Without a compile_commands.json clangd guesses .h is C++; default to C instead.
      clangd = { init_options = { fallbackFlags = { "-xc", "-std=gnu99" } } },
    },
  },
}
