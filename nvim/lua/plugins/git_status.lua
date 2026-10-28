-- VS Code style git status in the explorer and the <leader>gs picker:
-- a letter badge colored by change type. Staged vs unstaged doesn't change it.
local badges = {
  added = "A",
  untracked = "A",
  modified = "M",
  deleted = "D",
  renamed = "R",
  copied = "A",
  unmerged = "C", -- conflict
  ignored = "",
}

local hls = {
  added = "diffAdded",
  untracked = "diffAdded",
  modified = "DiagnosticWarn",
  deleted = "diffRemoved",
  renamed = "diffAdded",
  copied = "diffAdded",
  unmerged = "DiagnosticError",
  ignored = "NonText",
}

return {
  "folke/snacks.nvim",
  opts = function(_, opts)
    local format = require("snacks.picker.format")
    local git = require("snacks.picker.source.git")

    local function kind(xy)
      local s = git.git_status(xy)
      return s.unmerged and "unmerged" or s.status
    end

    -- explorer (and any file list): right-aligned badge, folders get a dot
    format.file_git_status = function(item, picker)
      local k = kind(item.status)
      if picker.opts.formatters.file.git_status_hl then
        item.filename_hl = hls[k]
      end
      local badge = (item.dir and k ~= "ignored") and "●" or badges[k]
      return {
        {
          col = 0,
          virt_text = { { badge, hls[k] }, { " " } },
          virt_text_pos = "right_align",
          hl_mode = "combine",
        },
      }
    end

    -- <leader>gs: replace the raw porcelain code (??, " M", ...) with the badge
    local git_status = format.git_status
    format.git_status = function(item, picker)
      local ret = git_status(item, picker)
      if item.status then -- git_diff hunks have no status, leave those alone
        local k = kind(item.status)
        ret[1] = { badges[k], hls[k] }
      end
      return ret
    end
  end,
}
