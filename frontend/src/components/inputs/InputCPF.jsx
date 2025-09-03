import React from "react";
import BaseInputField from "./BaseInputField";
import { cpfConfig } from "../../utils/inputHelpers.tsx";

const InputCPF = ({ label = "CPF", ...props }) => {
  return (
    <BaseInputField
      label={label}
      formatterConfig={cpfConfig.formatter}
      validatorConfig={cpfConfig.validator}
      leftIcon={cpfConfig.icon}
      placeholder={cpfConfig.placeholder}
      inputMode={cpfConfig.inputMode}
      autoComplete={cpfConfig.autoComplete}
      successMessage={cpfConfig.successMessage}
      progressMessage={cpfConfig.progressMessage}
      showProgressIndicator
      {...props}
    />
  );
};

export default InputCPF;
