-- soft-wrap markdown at 80 columns regardless of window width
return {
  "rickhowe/wrapwidth",
  ft = "markdown",
  config = function()
    local function apply(buf)
      vim.api.nvim_buf_call(buf, function()
        vim.cmd("Wrapwidth 80")
      end)
    end
    vim.api.nvim_create_autocmd("FileType", {
      pattern = "markdown",
      callback = function(ev)
        apply(ev.buf)
      end,
    })
    -- the FileType event that lazy-loaded this plugin has already fired
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      if vim.bo[buf].filetype == "markdown" then
        apply(buf)
      end
    end
  end,
}
