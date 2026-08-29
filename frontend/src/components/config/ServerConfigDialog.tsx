'use client';

import React from "react";
import { ServerProfileManagerDialog } from "./ServerProfileManagerDialog";

interface ServerConfigDialogProps {
  isOpen?: boolean;
  onClose?: () => void;
  onConfigured?: () => void;
}

export function ServerConfigDialog({ isOpen, onClose, onConfigured }: ServerConfigDialogProps) {
  return (
    <ServerProfileManagerDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfigured={onConfigured}
    />
  );
}
