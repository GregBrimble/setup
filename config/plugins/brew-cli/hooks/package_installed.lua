function PLUGIN:PackageInstalled(ctx)
    local brew = require("brew")
    local installed = {}
    local results = {}
    for _, pkg in ipairs(ctx.packages) do
        local kind, name = brew.package(pkg.name)
        if not installed[kind] then
            installed[kind] = brew.installed(kind)
        end
        local version = installed[kind][name]
        table.insert(results, {
            name = pkg.name,
            state = version and "installed" or "missing",
            version = version,
        })
    end
    return { packages = results }
end
