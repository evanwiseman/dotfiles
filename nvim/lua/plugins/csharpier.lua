-- C# formatting with CSharpier (the lang.dotnet extra already sets conform's cs = { "csharpier" }).
-- Repos that pin CSharpier in dotnet-tools.json get that exact version via `dotnet csharpier`, so
-- format-on-save matches CI; anywhere else falls back to Mason's csharpier. Decided per file, unlike
-- conform's built-in check, which runs once from nvim's startup directory and caches the answer.

---Repo root whose dotnet-tools.json pins csharpier, or nil.
---@param dirname string
---@return string?
local function csharpier_tool_root(dirname)
  local root = vim.fs.root(dirname, "dotnet-tools.json")
  if not root then
    return nil
  end
  local ok, lines = pcall(vim.fn.readfile, root .. "/dotnet-tools.json")
  if ok and table.concat(lines, "\n"):find('"csharpier"', 1, true) then
    return root
  end
  return nil
end

return {
  {
    "stevearc/conform.nvim",
    opts = {
      formatters = {
        csharpier = {
          command = function(_, ctx)
            return csharpier_tool_root(ctx.dirname) and "dotnet" or "csharpier"
          end,
          args = function(_, ctx)
            local args = { "format", "--stdin-path", "$FILENAME" }
            if csharpier_tool_root(ctx.dirname) then
              table.insert(args, 1, "csharpier")
            end
            return args
          end,
          -- Run from the repo root so `dotnet` resolves the repo's tool manifest.
          cwd = function(_, ctx)
            return csharpier_tool_root(ctx.dirname)
          end,
          stdin = true,
        },
      },
    },
  },
  {
    -- Fallback binary for repos without a pinned tool; keep it on the version dragon-control pins.
    "mason-org/mason.nvim",
    opts = { ensure_installed = { "csharpier" } },
  },
}
