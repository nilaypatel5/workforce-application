sap.ui.define(
  [
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageBox",
    "sap/m/MessageToast",
    "sap/ui/model/json/JSONModel",
    "sap/ui/core/Item",
    "sap/m/Dialog",
    "sap/m/Label",
    "sap/m/DatePicker",
    "sap/m/Select",
    "sap/m/TextArea",
    "sap/m/Button",
    "sap/m/VBox",
  ],
  function (
    Controller,
    MessageBox,
    MessageToast,
    JSONModel,
    Item,
    Dialog,
    Label,
    DatePicker,
    Select,
    TextArea,
    Button,
    VBox,
  ) {
    "use strict";

    return Controller.extend("my.app.controller.MyLeaves", {
      onInit: function () {
        const oModel = new JSONModel({
          items: [],
        });
        this.getView().setModel(oModel, "leavesModel");
        this.loadLeaves();
      },

      formatStatusState: function (sStatus) {
        if (!sStatus) {
          return "None";
        }
        const sUpper = sStatus.toUpperCase();
        if (sUpper === "PENDING") {
          return "Warning";
        }
        if (sUpper === "APPROVED") {
          return "Success";
        }
        if (sUpper === "REJECTED") {
          return "Error";
        }
        return "None";
      },

      onRefreshButtonPress: function () {
        this.loadLeaves();
      },

      ensureAuthenticated: function () {
        const token = localStorage.getItem("authToken");
        if (!token) {
          this.getOwnerComponent().getRouter().navTo("Login");
          return null;
        }
        return token;
      },

      loadLeaves: async function () {
        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        try {
          const res = await fetch("/api/ess/leaves", {
            method: "GET",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok || !Array.isArray(data)) {
            const sMessage =
              (data && (data.detail || data.message)) ||
              "Could not load leave requests.";
            MessageBox.error(sMessage);
            return;
          }

          const oModel = this.getView().getModel("leavesModel");
          oModel.setProperty("/items", data);
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      onRequestLeaveButtonPress: function () {
        if (this._oDialog) {
          this._oDialog.destroy();
          this._oDialog = null;
        }

        const oStartDate = new DatePicker({
          width: "100%",
        });
        const oEndDate = new DatePicker({
          width: "100%",
        });

        const oTypeSelect = new Select({ width: "100%" });
        oTypeSelect.addItem(new Item({ text: "Annual Leave", key: "Annual" }));
        oTypeSelect.addItem(new Item({ text: "Sick Leave", key: "Sick" }));
        oTypeSelect.addItem(new Item({ text: "Casual Leave", key: "Casual" }));
        oTypeSelect.addItem(new Item({ text: "Unpaid Leave", key: "Unpaid" }));

        const oReason = new TextArea({
          width: "100%",
          rows: 2,
          placeholder: "Reason (optional)",
        });

        const oContent = new sap.ui.layout.form.SimpleForm({
          editable: true,
          layout: "ResponsiveGridLayout",
          columnsL: 2,
          columnsM: 2,
          columnsS: 1,
          content: [
            new Label({ text: "Start Date" }),
            oStartDate,

            new Label({ text: "End Date" }),
            oEndDate,

            new Label({ text: "Leave Type" }),
            oTypeSelect,

            new Label({ text: "Reason" }),
            oReason,
          ],
        });

        const that = this;

        this._oDialog = new Dialog({
          title: "Request Leave",
          contentWidth: "50rem",
          contentHeight: "auto",
          content: [oContent],
          beginButton: new Button({
            text: "Submit",
            type: "Emphasized",
            press: async function () {
              await that.submitLeaveRequest({
                startDatePicker: oStartDate,
                endDatePicker: oEndDate,
                typeSelect: oTypeSelect,
                reasonField: oReason,
              });
            },
          }),
          endButton: new Button({
            text: "Cancel",
            press: function () {
              that._oDialog.close();
            },
          }),
          afterClose: function () {
            that._oDialog.destroy();
            that._oDialog = null;
          },
        });

        this.getView().addDependent(this._oDialog);
        this._oDialog.open();
      },
      submitLeaveRequest: async function (mControls) {
        const oStartDatePicker = mControls.startDatePicker;
        const oEndDatePicker = mControls.endDatePicker;
        const oTypeSelect = mControls.typeSelect;
        const oReasonField = mControls.reasonField;

        const oStartDate = oStartDatePicker.getDateValue();
        const oEndDate = oEndDatePicker.getDateValue();
        const sTypeKey = oTypeSelect.getSelectedKey();
        const sReason = oReasonField.getValue();

        if (!oStartDate || !oEndDate || !sTypeKey) {
          MessageBox.error("Please fill Start Date, End Date and Leave Type.");
          return;
        }

        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        const sStartDateIso = oStartDate.toISOString().slice(0, 10);
        const sEndDateIso = oEndDate.toISOString().slice(0, 10);

        try {
          const res = await fetch("/api/ess/leaves", {
            method: "POST",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              startDate: sStartDateIso,
              endDate: sEndDateIso,
              type: sTypeKey,
              reason: sReason,
            }),
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok) {
            const sMessage =
              (data && (data.detail || data.message)) ||
              "Could not create leave request.";
            MessageBox.error(sMessage);
            return;
          }

          if (this._oDialog) {
            this._oDialog.close();
          }

          MessageToast.show("Leave request created.");
          this.loadLeaves();
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },
    });
  },
);
