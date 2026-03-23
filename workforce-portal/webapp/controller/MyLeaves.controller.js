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
    "sap/ui/layout/form/SimpleForm",
    "sap/ui/unified/DateTypeRange",
    "sap/ui/unified/DateRange",
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
    SimpleForm,
    DateTypeRange,
    DateRange,
  ) {
    "use strict";

    return Controller.extend("my.app.controller.MyLeaves", {
      onInit: function () {
        const oModel = new JSONModel({
          items: [],
          dayLeaves: [],
          selectedDayLabel: "",
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
        if (sUpper === "CANCELLED" || sUpper === "CANCELED") {
          return "Information";
        }
        return "None";
      },

      formatAppointmentType: function (sStatus) {
        const s = (sStatus || "").toLowerCase();
        if (s === "approved") return "Type01";
        if (s === "pending") return "Type02";
        if (s === "rejected") return "Type03";
        if (s === "cancelled") return "Type04";
        return "None";
      },

      formatDateTime: function (sDateTime) {
        if (!sDateTime) return "—";
        const oDate = new Date(sDateTime);
        if (isNaN(oDate)) return sDateTime;
        return oDate.toLocaleString();
      },

      isPendingStatus: function (sStatus) {
        return (sStatus || "").trim().toLowerCase() === "pending";
      },

      onRefreshButtonPress: function () {
        this.loadLeaves();
      },

      parseLocalIsoDate: function (sIso) {
        if (!sIso || typeof sIso !== "string") {
          return null;
        }
        const parts = sIso.split("-");
        if (parts.length !== 3) {
          return null;
        }
        const y = parseInt(parts[0], 10);
        const m = parseInt(parts[1], 10);
        const d = parseInt(parts[2], 10);
        if (!y || !m || !d) {
          return null;
        }
        return new Date(y, m - 1, d);
      },

      normalizeKeyOrEmpty: function (sKey) {
        return (sKey || "").trim().toLowerCase() === "all" ? "" : sKey;
      },

      applyFiltersAndSort: function () {
        const oView = this.getView();

        const oStatusSelect = oView.byId("idFilterStatusSelect");
        const oTypeSelect = oView.byId("idFilterTypeSelect");
        const oFromDate = oView.byId("idFilterFromDatePicker");
        const oToDate = oView.byId("idFilterToDatePicker");
        const oSortSelect = oView.byId("idSortSelect");

        const statusKey = this.normalizeKeyOrEmpty(oStatusSelect.getSelectedKey());
        const typeKey = this.normalizeKeyOrEmpty(oTypeSelect.getSelectedKey());
        const sortBy = oSortSelect.getSelectedKey() || "startDesc";

        const dFrom = oFromDate.getDateValue();
        const dTo = oToDate.getDateValue();

        const filtered = (this.allLeaves || []).filter((oLeave) => {
          const dStart = this.parseLocalIsoDate(oLeave.startDate);
          const dEnd = this.parseLocalIsoDate(oLeave.endDate);

          if (!dStart || !dEnd) {
            return true;
          }

          if (statusKey) {
            if ((oLeave.status || "").trim().toLowerCase() !== statusKey.toLowerCase()) {
              return false;
            }
          }

          if (typeKey) {
            if ((oLeave.type || "").trim().toLowerCase() !== typeKey.toLowerCase()) {
              return false;
            }
          }

          if (dFrom) {
            if (dEnd < dFrom) {
              return false;
            }
          }

          if (dTo) {
            if (dStart > dTo) {
              return false;
            }
          }

          return true;
        });

        const toDateTime = function (sIso) {
          if (!sIso) return null;
          const d = new Date(sIso);
          return Number.isNaN(d.getTime()) ? null : d;
        };

        const sorted = filtered.sort((a, b) => {
          if (sortBy === "startAsc") {
            const da = this.parseLocalIsoDate(a.startDate);
            const db = this.parseLocalIsoDate(b.startDate);
            return (da && db ? da - db : 0) || 0;
          }

          if (sortBy === "createdDesc") {
            const da = toDateTime(a.createdAt);
            const db = toDateTime(b.createdAt);
            return (da && db ? db - da : 0) || 0;
          }

          const da = this.parseLocalIsoDate(a.startDate);
          const db = this.parseLocalIsoDate(b.startDate);
          return (da && db ? db - da : 0) || 0;
        });

        const oModel = oView.getModel("leavesModel");
        oModel.setProperty("/items", sorted);
      },

      _syncMonthCalendar: function () {
        const oCal = this.byId("idMonthCalendar");
        if (!oCal) {
          return;
        }
        oCal.removeAllSpecialDates();
        const leaves = this.allLeaves || [];
        const that = this;
        leaves.forEach(function (oLeave) {
          const s = that.parseLocalIsoDate(oLeave.startDate);
          const e = that.parseLocalIsoDate(oLeave.endDate);
          if (!s || !e) {
            return;
          }
          const dr = new DateTypeRange({
            startDate: s,
            endDate: e,
            type: that.formatAppointmentType(oLeave.status),
          });
          oCal.addSpecialDate(dr);
        });
      },

      _setDayLeavesForDate: function (d) {
        if (!d) {
          return;
        }
        const t = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        const leaves = (this.allLeaves || []).filter(function (oLeave) {
          const s = this.parseLocalIsoDate(oLeave.startDate);
          const e = this.parseLocalIsoDate(oLeave.endDate);
          if (!s || !e) {
            return false;
          }
          const s0 = new Date(s.getFullYear(), s.getMonth(), s.getDate());
          const e0 = new Date(e.getFullYear(), e.getMonth(), e.getDate());
          return t >= s0 && t <= e0;
        }.bind(this));
        const oModel = this.getView().getModel("leavesModel");
        oModel.setProperty("/dayLeaves", leaves);
        oModel.setProperty(
          "/selectedDayLabel",
          "Leaves on " +
            d.toLocaleDateString(undefined, {
              weekday: "short",
              year: "numeric",
              month: "short",
              day: "numeric",
            }),
        );
      },

      onCalendarMonthSelect: function (oEvent) {
        const oCal = oEvent.getSource();
        const aDates = oCal.getSelectedDates();
        let d = null;
        if (aDates && aDates.length > 0 && aDates[0].getStartDate) {
          d = aDates[0].getStartDate();
        }
        if (!d) {
          d =
            oEvent.getParameter("date") || oEvent.getParameter("startDate");
        }
        if (d) {
          this._setDayLeavesForDate(d);
        }
      },

      onCalendarMonthStartDateChange: function () {
        this._syncMonthCalendar();
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

          this.allLeaves = data;
          this.applyFiltersAndSort();
          this._syncMonthCalendar();
          const oCal = this.byId("idMonthCalendar");
          const today = new Date();
          if (oCal) {
            oCal.removeAllSelectedDates();
            oCal.addSelectedDate(new DateRange({ startDate: today }));
          }
          this._setDayLeavesForDate(today);
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      onApplyButtonPress: function () {
        this.applyFiltersAndSort();
        this._syncMonthCalendar();
      },

      onClearButtonPress: function () {
        const oView = this.getView();
        oView.byId("idFilterStatusSelect").setSelectedKey("All");
        oView.byId("idFilterTypeSelect").setSelectedKey("All");
        oView.byId("idFilterFromDatePicker").setDateValue(null);
        oView.byId("idFilterToDatePicker").setDateValue(null);
        oView.byId("idSortSelect").setSelectedKey("startDesc");

        this.applyFiltersAndSort();
        this._syncMonthCalendar();
      },

      onRequestLeaveButtonPress: function () {
        if (this.oDialog) {
          this.oDialog.destroy();
          this.oDialog = null;
        }

        const oStartDate = new DatePicker({
          width: "100%",
        });
        const oEndDate = new DatePicker({
          width: "100%",
        });

        const oTypeSelect = new Select({ width: "100%" });
        oTypeSelect.addItem(new Item({ text: "Select type", key: "" }));
        oTypeSelect.addItem(new Item({ text: "Annual Leave", key: "Annual" }));
        oTypeSelect.addItem(new Item({ text: "Sick Leave", key: "Sick" }));
        oTypeSelect.addItem(new Item({ text: "Casual Leave", key: "Casual" }));
        oTypeSelect.addItem(new Item({ text: "Unpaid Leave", key: "Unpaid" }));
        oTypeSelect.setSelectedKey("");

        const oReason = new TextArea({
          width: "100%",
          rows: 2,
          placeholder: "Reason (optional)",
        });

        const oContent = new SimpleForm({
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

        this.oDialog = new Dialog({
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
              that.oDialog.close();
            },
          }),
          afterClose: function () {
            that.oDialog.destroy();
            that.oDialog = null;
          },
        });

        this.getView().addDependent(this.oDialog);
        this.oDialog.open();
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

        if (!oStartDate) {
          MessageBox.error("Start Date is required.");
          return;
        }
        if (!oEndDate) {
          MessageBox.error("End Date is required.");
          return;
        }
        if (!sTypeKey) {
          MessageBox.error("Leave Type is required.");
          return;
        }
        if (oEndDate < oStartDate) {
          MessageBox.error("End Date cannot be before Start Date.");
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

          if (this.oDialog) {
            this.oDialog.close();
          }

          MessageToast.show("Leave request created.");
          this.loadLeaves();
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      onCancelButtonPress: function (oEvent) {
        const oSource = oEvent.getSource();
        const oCtx = oSource.getBindingContext("leavesModel");
        const oRow = oCtx && oCtx.getObject();
        const nId = oRow && oRow.id;

        if (!nId) {
          MessageBox.error("Could not determine leave request ID.");
          return;
        }

        if (!this.isPendingStatus(oRow.status)) {
          MessageBox.error("Only Pending leave requests can be cancelled.");
          return;
        }

        const that = this;
        MessageBox.confirm("Cancel this leave request?", {
          actions: [MessageBox.Action.OK, MessageBox.Action.CANCEL],
          emphasizedAction: MessageBox.Action.OK,
          onClose: async function (sAction) {
            if (sAction !== MessageBox.Action.OK) {
              return;
            }
            await that.cancelLeaveRequest(nId);
          },
        });
      },

      cancelLeaveRequest: async function (nId) {
        const token = this.ensureAuthenticated();
        if (!token) {
          return;
        }

        try {
          const res = await fetch("/api/ess/leaves/" + nId + "/cancel", {
            method: "PUT",
            headers: {
              Authorization: "Bearer " + token,
              "Content-Type": "application/json",
            },
          });

          const data = await res.json().catch(function () {
            return null;
          });

          if (!res.ok) {
            const sMessage =
              (data && (data.detail || data.message)) ||
              "Could not cancel leave request.";
            MessageBox.error(sMessage);
            return;
          }

          MessageToast.show("Leave request cancelled.");
          this.loadLeaves();
        } catch (e) {
          MessageBox.error(
            "Cannot reach backend service. Please check if the Flask server is running.",
          );
        }
      },

      onColumnListItemPress: function (oEvent) {
        const that = this;
        const oSource = oEvent.getSource();
        const oCtx = oSource.getBindingContext("leavesModel");
        const oLeave = oCtx && oCtx.getObject();

        if (!oLeave) {
          MessageBox.error("Could not load leave details.");
          return;
        }

        if (this.oDetailsDialog) {
          this.oDetailsDialog.destroy();
          this.oDetailsDialog = null;
        }

        const oContent = new SimpleForm({
          editable: false,
          layout: "ResponsiveGridLayout",
          columnsL: 2,
          columnsM: 2,
          content: [
            new sap.m.Label({ text: "Leave ID" }),
            new sap.m.Text({ text: String(oLeave.id || "") }),

            new sap.m.Label({ text: "Start Date" }),
            new sap.m.Text({ text: oLeave.startDate || "" }),

            new sap.m.Label({ text: "End Date" }),
            new sap.m.Text({ text: oLeave.endDate || "" }),

            new sap.m.Label({ text: "Type" }),
            new sap.m.Text({ text: oLeave.type || "" }),

            new sap.m.Label({ text: "Status" }),
            new sap.m.Text({ text: oLeave.status || "" }),

            new sap.m.Label({ text: "Reason" }),
            new sap.m.Text({ text: oLeave.reason || "—" }),

            new sap.m.Label({ text: "Created At" }),
            new sap.m.Text({
              text: this.formatDateTime(oLeave.createdAt),
            }),

            new sap.m.Label({ text: "Manager comment" }),
            new sap.m.Text({ text: oLeave.managerComment || "—" }),

            new sap.m.Label({ text: "Approved At" }),
            new sap.m.Text({
              text: oLeave.approvedAt
                ? this.formatDateTime(oLeave.approvedAt)
                : "—",
            }),

            new sap.m.Label({ text: "Rejected At" }),
            new sap.m.Text({
              text: oLeave.rejectedAt
                ? this.formatDateTime(oLeave.rejectedAt)
                : "—",
            }),
          ],
        });

        this.oDetailsDialog = new Dialog({
          title: "Leave Details",
          contentWidth: "30rem",
          content: [oContent],
          endButton: new Button({
            text: "Close",
            press: function () {
              that.oDetailsDialog && that.oDetailsDialog.close();
            },
          }),
          afterClose: function () {
            if (that.oDetailsDialog) {
              that.oDetailsDialog.destroy();
              that.oDetailsDialog = null;
            }
          },
        });

        this.getView().addDependent(this.oDetailsDialog);
        this.oDetailsDialog.open();
      },
    });
  },
);