# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settingsUI.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(301, 569)
        self.gridLayout_2 = QGridLayout(Form)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.checkBox_enable_sliding = QGroupBox(Form)
        self.checkBox_enable_sliding.setObjectName(u"checkBox_enable_sliding")
        self.checkBox_enable_sliding.setCheckable(True)
        self.gridLayout_3 = QGridLayout(self.checkBox_enable_sliding)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.label = QLabel(self.checkBox_enable_sliding)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.lineEdit_sliding_object = QLineEdit(self.checkBox_enable_sliding)
        self.lineEdit_sliding_object.setObjectName(u"lineEdit_sliding_object")

        self.gridLayout.addWidget(self.lineEdit_sliding_object, 1, 1, 1, 1)

        self.spinBox_loop_amount = QSpinBox(self.checkBox_enable_sliding)
        self.spinBox_loop_amount.setObjectName(u"spinBox_loop_amount")
        self.spinBox_loop_amount.setMinimum(1)
        self.spinBox_loop_amount.setValue(1)

        self.gridLayout.addWidget(self.spinBox_loop_amount, 0, 1, 1, 1)

        self.label_2 = QLabel(self.checkBox_enable_sliding)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)


        self.gridLayout_3.addLayout(self.gridLayout, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.checkBox_enable_sliding, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.checkBox_enable_zipper = QCheckBox(Form)
        self.checkBox_enable_zipper.setObjectName(u"checkBox_enable_zipper")
        self.checkBox_enable_zipper.setEnabled(False)

        self.gridLayout_2.addWidget(self.checkBox_enable_zipper, 0, 0, 1, 1)

        self.checkBox_auto_pinch = QCheckBox(Form)
        self.checkBox_auto_pinch.setObjectName(u"checkBox_auto_pinch")

        self.gridLayout_2.addWidget(self.checkBox_auto_pinch, 1, 0, 1, 1)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.gridLayout_2.addWidget(self.line, 2, 0, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.checkBox_enable_sliding.setTitle(QCoreApplication.translate("Form", u"Enable Sliding", None))
        self.label.setText(QCoreApplication.translate("Form", u"Loop Amount", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Sliding Mesh", None))
        self.checkBox_enable_zipper.setText(QCoreApplication.translate("Form", u"Enable Zipper", None))
        self.checkBox_auto_pinch.setText(QCoreApplication.translate("Form", u"Auto Pinch", None))
    # retranslateUi

