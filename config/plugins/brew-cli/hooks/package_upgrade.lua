function PLUGIN:PackageUpgrade(ctx)
    require("brew").apply(ctx, "upgrade")
end
