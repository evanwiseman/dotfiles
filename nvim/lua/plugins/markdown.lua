-- Markdown tweaks on top of lazyvim.plugins.extras.lang.markdown
local markdownlint_config = vim.fn.stdpath("config") .. "/.markdownlint-cli2.yaml"

return {
  {
    "MeanderingProgrammer/render-markdown.nvim",
    opts = {
      -- show raw markdown on the cursor line only, rendered everywhere else
      anti_conceal = { enabled = true },
      heading = {
        icons = { "󰲡 ", "󰲣 ", "󰲥 ", "󰲧 ", "󰲩 ", "󰲫 " },
        width = "block",
        right_pad = 1,
      },
      bullet = { icons = { "●", "○", "◆", "◇" } },
      checkbox = {
        enabled = true,
        unchecked = { icon = "󰄱 " },
        checked = { icon = "󰱒 " },
      },
      pipe_table = { preset = "round" },
    },
  },
  {
    "mfussenegger/nvim-lint",
    optional = true,
    opts = {
      linters = {
        ["markdownlint-cli2"] = { args = { "--config", markdownlint_config, "-" } },
      },
    },
  },
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = {
      formatters = {
        ["markdownlint-cli2"] = { prepend_args = { "--config", markdownlint_config } },
      },
    },
  },
}
