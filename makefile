DEVICES := mcxn947 mcxn547

CHIPTOOL_REV := 4eb4feb74bd469a1c8244364b9adc3b7f3e9404d

CHIPTOOL := chiptool
SVDTOOLS := svdtools

# Files
ORIGINAL_SVDS := $(foreach device, $(DEVICES), svds/$(device)/svd)
PATCH_FILES := $(foreach device, $(DEVICES), svds/$(device).yaml)

PATCHED_SVDS := $(foreach device, $(DEVICES), svds/$(device).svd.patched)
DEVICE_PERIPHERALS_DIRS := $(foreach device, $(DEVICES), temp/$(device))

.PHONY: install-tools patch extract-peripherals transform clean clean-patch clean-extracted-peripherals clean-peripherals

install-tools:
	@echo "Install tools"
	@cargo install svdtools@0.3.14
	@cargo install --git https://github.com/mcx-rs/chiptool --rev $(CHIPTOOL_REV)

patch: $(PATCHED_SVDS)
svds/%.svd.patched: svds/%.yaml svds/%.svd
	@echo "Patch $*"
	@$(SVDTOOLS) patch $< $@

extract-peripherals: $(DEVICE_PERIPHERALS_DIRS)
temp/%: svds/%.svd.patched
	@echo "Extract Peripherals from $*"
	@$(CHIPTOOL) extract-all --svd $< --output $@

transform: extract-peripherals
	@echo "Transform peripherals"
	@rm -rf peripherals
	@python3 -c "from scripts.peripherals import copy_and_rename_peripherals, apply_transform; copy_and_rename_peripherals(); apply_transform()"

clean: clean-patch clean-extracted-peripherals clean-peripherals
clean-patch:
	@echo "Clean patched svds"
	@rm -f $(PATCHED_SVDS)
clean-extracted-peripherals:
	@echo "Clean extracted peripherals"
	@rm -rf temp
clean-peripherals:
	@rm -rf peripherals
