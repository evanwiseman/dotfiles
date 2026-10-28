return {
  -- Configure LSP servers
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        basedpyright = {
          settings = {
            basedpyright = {
              -- Disable organize imports if you want Ruff to handle import sorting
              disableOrganizeImports = true,
              analysis = {
                typeCheckingMode = "standard", -- or "basic", "all"
                -- If you want basedpyright to skip lint-like diagnostics that ruff covers:
                -- ignore = { "*" },
              },
            },
          },
        },
        ruff = {
          init_options = {
            settings = {
              -- Add any custom ruff-specific settings here if not using pyproject.toml
              args = {},
            },
          },
        },
      },
    },
  },
}
